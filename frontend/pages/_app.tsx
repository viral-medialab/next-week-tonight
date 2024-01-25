import "dotenv/config";
import "@/styles/globals.css";
import type { AppProps } from "next/app";
import HeaderTopic from "@/components/HeaderTopic";
import { useRouter } from "next/router";
export default function App({ Component, pageProps }: AppProps) {
    const router = useRouter();
    return (
        <div className={`h-screen ${router.pathname === "/" ? "" : "pt-20"}`}>
            {router.pathname !== "/" && <HeaderTopic />}
            <Component {...pageProps} />
        </div>
    );
}
