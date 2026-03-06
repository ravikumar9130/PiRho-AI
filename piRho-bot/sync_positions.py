#!/usr/bin/env python3
"""
Sync Existing Positions from Bybit to Database

Run this script to import open positions from Bybit into the Supabase trades table.
This is a one-time sync for positions opened before the database integration.
"""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Bybit API imports
from bybit_client import BybitClient

async def sync_positions():
    """Sync open Bybit positions to the trades database."""
    
    print("=" * 60)
    print("Position Sync: Bybit → Database")
    print("=" * 60)
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all bots and their credentials
    print("\n📡 Fetching bots from database...")
    result = supabase.table('bots').select(
        '*, tenants!inner(id, user_id, exchange_credentials(*))'
    ).execute()
    
    if not result.data:
        print("No bots found in database")
        return
    
    # Decrypt function (simplified - assumes credentials are encrypted)
    from cryptography.fernet import Fernet
    encryption_key = os.getenv('ENCRYPTION_KEY')
    if encryption_key:
        fernet = Fernet(encryption_key.encode())
        
        def decrypt(value):
            try:
                return fernet.decrypt(value.encode()).decode()
            except:
                return value
    else:
        decrypt = lambda x: x
    
    positions_synced = 0
    
    for bot in result.data:
        bot_id = bot['id']
        tenant_id = bot['tenant_id']
        symbol = bot['symbol']
        strategy = bot['strategy']
        
        tenant = bot.get('tenants', {})
        credentials_list = tenant.get('exchange_credentials', [])
        
        if not credentials_list:
            print(f"⚠️  Bot {bot['name']} has no credentials, skipping")
            continue
        
        cred = credentials_list[0]
        
        try:
            api_key = decrypt(cred['encrypted_api_key'])
            api_secret = decrypt(cred['encrypted_api_secret'])
            is_testnet = cred.get('is_testnet', True)
            
            print(f"\n🤖 Bot: {bot['name']} ({symbol})")
            
            # Initialize Bybit client
            client = BybitClient({
                'bybit': {
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'testnet': is_testnet
                }
            })
            
            # Get open positions from Bybit
            positions = await client.get_positions(symbol)
            
            for pos in positions:
                size = float(pos.get('size', 0))
                if size == 0:
                    continue
                
                side = pos.get('side', 'Buy')
                entry_price = float(pos.get('avgPrice', 0) or pos.get('entryPrice', 0))
                leverage = int(float(pos.get('leverage', 1) or 1))
                
                print(f"   📊 Found position: {side} {size} @ ${entry_price:.2f}")
                
                # Check if this position is already in the database
                existing = supabase.table('trades').select('id').eq(
                    'bot_id', bot_id
                ).eq('symbol', symbol).is_('closed_at', 'null').execute()
                
                if existing.data:
                    print(f"   ℹ️  Position already exists in database (id: {existing.data[0]['id']})")
                    continue
                
                # Insert the position
                trade_record = {
                    'tenant_id': tenant_id,
                    'bot_id': bot_id,
                    'symbol': symbol,
                    'side': 'BUY' if side == 'Buy' else 'SELL',
                    'entry_price': entry_price,
                    'quantity': size,
                    'leverage': leverage,
                    'strategy': strategy,
                    'opened_at': datetime.now(timezone.utc).isoformat(),  # Approximate
                    'closed_at': None,  # Open position
                    'is_paper': is_testnet,  # Assume testnet = paper
                    'metadata': {
                        'synced_from_bybit': True,
                        'sync_time': datetime.now(timezone.utc).isoformat(),
                        'bybit_data': pos
                    }
                }
                
                insert_result = supabase.table('trades').insert(trade_record).execute()
                
                if insert_result.data:
                    positions_synced += 1
                    print(f"   ✅ Position synced to database (id: {insert_result.data[0]['id']})")
                else:
                    print(f"   ❌ Failed to sync position")
                    
        except Exception as e:
            print(f"   ❌ Error processing bot {bot['name']}: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Sync complete! {positions_synced} position(s) synced.")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(sync_positions())

