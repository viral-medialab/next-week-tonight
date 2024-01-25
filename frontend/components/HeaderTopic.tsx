import Link from "next/link";
import { useRouter } from "next/router";

const HeaderTopic = () => {
    const router = useRouter();
    const currentTopicId = router.query.id as string;
    const isActive = (path: string) => {
        return router.pathname === path
            ? "text-gray-900 font-bold bg-red-100"
            : "text-gray-500";
    };

    console.log(
        "currentTopicId",
        currentTopicId,
        "router.pathname",
        router.pathname
    );

    return (
        <div className="bg-white shadow absolute top-0 inset-x-0 z-10">
            <div className="container mx-auto py-6 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
                <div className="flex items-center">
                    <Link
                        className="text-gray-800 font-bold text-xl tracking-tight hover:text-gray-600"
                        href="/"
                    >
                        Next Week Tonight
                    </Link>
                </div>
                {/*
                <nav className=" md:block">
                    <ul className="ml-10 flex items-baseline space-x-4">
                        <li>
                            <Link
                                className={`hover:text-gray-600 ${isActive(
                                    "/chat/[id]"
                                )}`}
                                href={`/chat/${currentTopicId}`}
                            >
                                Read and Chat
                            </Link>
                        </li>
                        <li>
                            <Link
                                className={`hover:text-gray-600 ${isActive(
                                    "/facts/[id]"
                                )}`}
                                href={`/facts/${currentTopicId}`}
                            >
                                Explore Claims
                            </Link>
                        </li>
                        <li>
                            <Link
                                className={`hover:text-gray-600 ${isActive(
                                    "/sources/[id]"
                                )}`}
                                href={`/sources/${currentTopicId}`}
                            >
                                Explore Sources
                            </Link>
                        </li>
                    </ul>
                </nav>
                */}
            </div>
        </div>
    );
};

export default HeaderTopic;
