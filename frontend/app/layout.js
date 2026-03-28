import { Inter, Manrope } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body"
});

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-headline"
});

export const metadata = {
  title: "TrustSphere SOC",
  description: "Frontend prototype for the TrustSphere SOC analyst experience."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${manrope.variable}`}>{children}</body>
    </html>
  );
}
