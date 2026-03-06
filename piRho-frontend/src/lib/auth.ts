import { AuthOptions, User } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { api } from "@/lib/api";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    refreshToken?: string;
    user: {
      id: string;
      email: string;
      name?: string;
    };
  }
  
  interface User {
    id: string;
    email: string;
    name?: string;
    accessToken: string;
    refreshToken: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    error?: string;
    user?: {
      id: string;
      email: string;
      name?: string;
    };
  }
}

async function refreshAccessToken(token: any) {
  try {
    const response = await api.refresh(token.refreshToken);
    return {
      ...token,
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
      accessTokenExpires: Date.now() + 14 * 60 * 1000,
    };
  } catch (error) {
    console.error("Failed to refresh token:", error);
    return { ...token, error: "RefreshAccessTokenError" };
  }
}

export const authOptions: AuthOptions = {
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
        isRegister: { label: "Register", type: "text" },
        name: { label: "Name", type: "text" },
        promoCode: { label: "Promo Code", type: "text" },
      },
      async authorize(credentials): Promise<User | null> {
        if (!credentials?.email || !credentials?.password) {
          throw new Error("Email and password required");
        }

        try {
          let response;
          if (credentials.isRegister === "true") {
            response = await api.register({
              email: credentials.email,
              password: credentials.password,
              name: credentials.name || undefined,
              promo_code: credentials.promoCode || undefined,
            });
          } else {
            response = await api.login({
              email: credentials.email,
              password: credentials.password,
            });
          }

          // Decode JWT to get user info
          const payload = JSON.parse(atob(response.access_token.split(".")[1]));

          return {
            id: payload.sub,
            email: payload.email,
            name: credentials.name || payload.email.split("@")[0],
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
          };
        } catch (error: any) {
          console.error("Auth error:", error);
          throw new Error(error.message || "Authentication failed");
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      // Initial sign in
      if (user) {
        return {
          accessToken: user.accessToken,
          refreshToken: user.refreshToken,
          accessTokenExpires: Date.now() + 14 * 60 * 1000,
          user: {
            id: user.id,
            email: user.email,
            name: user.name,
          },
        };
      }

      // Return previous token if not expired
      if (Date.now() < (token.accessTokenExpires || 0)) {
        return token;
      }

      // Access token expired, refresh it
      return refreshAccessToken(token);
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      session.refreshToken = token.refreshToken;
      if (token.user) {
        session.user = token.user as any;
      }
      if (token.error) {
        // Force sign out on refresh error
        return { ...session, error: token.error };
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
    error: "/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 7 * 24 * 60 * 60, // 7 days
  },
  debug: process.env.NODE_ENV === "development",
};

