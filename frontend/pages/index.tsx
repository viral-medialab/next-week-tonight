import "dotenv/config";
import Head from "next/head";
import { useState, useEffect } from "react";
import { Ring } from "@uiball/loaders";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import Chat from "@/components/Chat";

const notifyArticleUpdate = () => {
    // Incrementing the updateTrigger will trigger the useEffect
  };

import {
    faPlus,
    faTrash,
    faThumbtack,
} from "@fortawesome/free-solid-svg-icons";
import TrackTopicButton from "@/components/TrackTopicButton";

type Topic = {
    _id: string;
    topic: string;
    isArticlesProcessed: boolean;
    createdAt: string;
    isTrackedTopic: boolean;
    isPinnedTopic: boolean;
};

const Index = () => {
    const [newsTopics, setNewsTopics] = useState<Topic[]>([]);
    const [isLoadingHeadlines, setIsLoadingHeadlines] = useState(true);
    const [isLoadingTrackedTopics, setIsLoadingTrackedTopics] = useState(true);
    const [urlId, seturlId] = useState(null);
    const [newsTopic, setNewsTopic] = useState(null);
    const [articleTitle, setArticleTitle] = useState("");
    const [articleContents, setArticleContents] = useState("");

    const getTopics = () => {
        fetch("/api/news")
            .then((res) => res.json())
            .then((data) => {
                console.log(data);
                setNewsTopics(data);
                setIsLoadingHeadlines(false);
            })
            .catch((err) => {
                console.log(err);
            });
    };

    const handleTopicClick = (topicId) => {
        seturlId(topicId);
    };

    useEffect(() => {
        const fetchNewsByTopicId = async () => {
            try {
                const response = await fetch("/api/getNewsByTopicId", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ topicId: urlId }),
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                // Assuming data contains a list of articles
                console.log("fetched topic");
                console.log(urlId);
                setNewsTopic(data);
            } catch (error) {
                console.error("Error fetching news by topic ID:", error);
            }
        };

        fetchNewsByTopicId();
    }, [urlId]);

    useEffect(() => {
        const fetchArticleInfo = async () => {
            try {
                if (newsTopic && newsTopic.articles && newsTopic.articles.length > 0) {
                    const firstArticleId = newsTopic.articles[0].id;
                    const response = await fetch("http://127.0.0.1:5000/api/gather_article_info", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            article_id: firstArticleId,
                        }),
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    console.log("Retrieved first article");
                    console.log(data.title);
                    seturlId(firstArticleId);
                    setArticleTitle(data.title);
                    setArticleContents(data.contents);
                } else {
                    console.log("No articles available for the topic");
                }
            } catch (error) {
                console.error("Error fetching article info:", error);
            }
        };

        fetchArticleInfo();
    }, [newsTopic]);

    useEffect(() => {
        console.log("i fire once");
        getTopics();
    }, []);

    const handleWelcomeClick = () => {
        window.location.href = "/";
    };

    return (
        <>
            <Head>
                <title>Next Week Tonight</title>
                <meta
                    name="Next Week Tonight"
                    content="Using Generative AI to Shape Tomorrow's Headlines"
                />
            </Head>
            <div className="w-full h-1/6 bg-gradient-to-br from-purple-400 to-purple-900">
                <div className="flex items-center justify-center h-full text-center">
                    <div onClick={() => handleWelcomeClick()} style={{ cursor: "pointer" }}>
                        <h1 className="text-4xl font-bold text-white mb-2">
                            Welcome to YOUR Next Week Tonight
                        </h1>
                        <h2 className="text-2xl text-gray-300">
                            Using Generative AI to Shape Tomorrow's Headlines
                        </h2>
                    </div>
                </div>
            </div>
            <div className="flex flex-col h-1/2">
                <div className="flex flex-1 h-1/2">
                    <div className="w-1/4 bg-gray-200 p-4 overflow-y-auto">
                        <h2 className="text-2xl font-bold">Headlines Today</h2>
                        <h3 className="text-lg font-medium text-gray-700 mb-4">
                            {new Date().toLocaleDateString("en-US", {
                                year: "numeric",
                                month: "long",
                                day: "numeric",
                            })}
                        </h3>
                        <ul className="space-y-2">
                            {newsTopics.map((topic) => (
                                <li key={topic._id}>
                                    <a
                                        href="#"
                                        onClick={() => handleTopicClick(topic._id)}
                                        className="text-blue-500 hover:text-blue-700"
                                    >
                                        {topic.topic}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="w-3/4 overflow-y-auto">
                        <div className="p-4 sm:p-6 lg:p-8">
                            <h1 id={articleTitle || ""} className="text-2xl font-bold text-gray-800 mb-4">
                                {articleTitle}
                            </h1>
                            <div
                                className="prose max-w-none"
                                dangerouslySetInnerHTML={{ __html: articleContents || "" }}
                            />
                        </div>
                    </div>
                </div>
            </div>

            <div className="w-full h-px bg-gray-900"></div>

            <div className="w-full">
                <Chat currentArticle={urlId}
                updateSidebarPredictions={notifyArticleUpdate}/>
            </div>
        </>
    );
};

export default Index;
