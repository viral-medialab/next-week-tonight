import "dotenv/config";
import Head from "next/head";
import { useState, useEffect } from "react";
import { Ring } from "@uiball/loaders";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import ChatCopy from "@/components/ChatCopy";

import {
    faPlus,
    faTrash,
    faThumbtack,
} from "@fortawesome/free-solid-svg-icons";
// import TrackTopicButton from "@/components/TrackTopicButton";

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
    const [currentArticle, setCurrentArticle] = useState({id: null, url: null});
    const [newsTopic, setNewsTopic] = useState(null);
    const [articleTitle, setArticleTitle] = useState("");
    const [articleContents, setArticleContents] = useState("");

    const getTopics = () => {
        fetch("/api/news")
            .then((res) => res.json())
            .then((data) => {
                console.log("frontend fetched")
                console.log(data);
                setNewsTopics(data);
                setIsLoadingHeadlines(false);
            })
            .catch((err) => {
                console.log(err);
            });
    };

    const handleTopicClick = (topicId) => {
        console.log("handleTopicClick called. Setting urlId to: ", topicId);
        seturlId(topicId);
    };

    useEffect(() => {
        const fetchNewsByTopicId = async () => {
            try {
                //const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:5000'; 
                const response = await fetch("api/getNewsByTopicId", {
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
                console.log("fetched topic: ", data);
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
                    console.log("fetchArticleInfo: Setting urlId to firstArticleId: ", firstArticleId);
                    const firstArticleUrl = newsTopic.articles[0].url;
                    //console.log(`first article url ${firstArticleUrl}`);
                    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:5000'; // Fallback URL
                    const response = await fetch(`${backendUrl}/api/gather_article_info`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        credentials: 'include', // Add this line

                        body: JSON.stringify({
                            article_id: firstArticleId,
                            articleUrl: firstArticleUrl
                        }),
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    console.log("Retrieved first article");
                    console.log(data.title);
                    seturlId(firstArticleId);
                    setCurrentArticle({id: firstArticleId, url: firstArticleUrl});
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

    // Add this log in the render function
    console.log("Rendering Index component. Current urlId:", urlId);

    return (
        <>
            <Head>
                <title>Next Week Tonight</title>
                <meta name="Next Week Tonight" content="Using Generative AI to Shape Tomorrow's Headlines" />
            </Head>
            <div className="w-full bg-white flex items-center h-1/6">
                <img src="/next_week_tonight_horizontal.png" alt="Next Week Tonight Logo" style={{ height: '50%', marginLeft: '40px' }} /> 
            </div>
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 h-1/2">
                <div className="flex h-full">
                    {/* Sidebar Component */}
                    <div className="w-1/4 bg-gray-200 p-4 overflow-y-auto">
                        <h2 className="text-2xl font-bold">News Story</h2>
                        <ul className="space-y-2">
                            {newsTopics.map((topic) => (
                                <li key={topic._id}>
                                    <a
                                        href="#"
                                        onClick={() => handleTopicClick(topic._id)}
                                        className="text-blue-500 hover:text-blue-700 block p-2"
                                    >
                                        {topic.topic}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Article Display Component */}
                    <div className="w-3/4 overflow-y-auto">
                        <div className="p-4 sm:p-6 lg:p-8">
                            <h1 id={articleTitle || ""} className="text-2xl font-bold text-gray-800 mb-4">
                                {articleTitle}
                            </h1>
                            {/* Add probability and impact display */}
                            {/* {newsTopic && newsTopic.articles && newsTopic.articles.length > 0 && (
                                <div>
                                    <p>Probability: {newsTopic.articles[0].probability}</p>
                                    <p>Impact: {newsTopic.articles[0].impact}</p>
                                </div>
                            )} */}
                            <div
                                className="prose max-w-none"
                                dangerouslySetInnerHTML={{ __html: articleContents || "" }}
                            />
                        </div>
                    </div>
                </div>
            </div>
            <div className="max-w-6xl mx-auto">
                {currentArticle.id && currentArticle.url && (
                    <ChatCopy currentArticle={currentArticle} />
                )}
            </div>
        </>
    );
};

export default Index;
