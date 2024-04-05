import "dotenv/config";
import Head from "next/head";
import { useState, useEffect } from "react";
import { Ring } from "@uiball/loaders";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import ChatCopy from "@/components/ChatCopy";
import { useRouter } from "next/router";

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
    const router = useRouter();
    const { id: urlID } = "BB1kLizV"; // supposed to be router.query

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
    const setPinnedTopic = (topicId: string) => {
        fetch(`/api/setPinnedTopic`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ pinnedTopicId: topicId }),
        })
            .then((res) => res.json())
            .then((data) => {
                console.log(data);
                getTopics();
            })
            .catch((err) => {
                console.log(err);
            });
    };
    const deleteTrackedTopic = (
        trackedTopicId: string,
        isPinnedTopic: boolean
    ) => {
        fetch(`/api/deleteTrackedTopic`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ trackedTopicId, isPinnedTopic }),
        })
            .then((res) => res.json())
            .then((data) => {
                console.log(data);
                getTopics();
            })
            .catch((err) => {
                console.log(err);
            });
    };

    useEffect(() => {
        console.log("i fire once");
        getTopics();
    }, []);

    return (
        <>
            <Head>
                <title>Next Week Tonight</title>
                <meta
                    name="Next Week Tonight"
                    content="Using Generative AI to Shape Tomorrow's Headlines"
                />
            </Head>
            <div className="flex">
                <div className="w-1/4 bg-gray-200 h-screen p-4">
                    <h2 className="text-2xl font-bold mb-4">Topics</h2>
                    <ul className="space-y-2">
                        {newsTopics.map((topic) => (
                            <li key={topic._id}>
                                <a
                                    href={`/topic/${topic._id}`}
                                    className="text-blue-500 hover:text-blue-700"
                                >
                                    {topic.topic}
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
                <div className="w-3/4 h-screen overflow-y-auto">
                    <div className="relative w-full h-1/4 bg-gradient-to-br from-purple-400 to-purple-900">
                        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center w-full">
                            <h1 className="text-4xl font-bold text-white mb-2">
                                Welcome to YOUR Next Week Tonight
                            </h1>
                            <h2 className="text-2xl  text-gray-300 mb-6">
                                Using Generative AI to Shape Tomorrow's Headlines
                            </h2>
                        </div>
                    </div>
                    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 mb-8">
                        <h2 className="text-2xl font-bold text-center">
                            Tracked Topics
                        </h2>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mt-6 mb-14">
                            {newsTopics
                                .filter(
                                    (trackedTopic) =>
                                        trackedTopic.topic &&
                                        (trackedTopic.isTrackedTopic ||
                                            trackedTopic.isPinnedTopic)
                                )
                                .map((trackedTopic) => (
                                    <div
                                        key={trackedTopic._id}
                                        className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 ease-in-out relative"
                                    >
                                        <div
                                            className="block p-4 pt-8"
                                            onClick={() =>
                                                window.location.href = `/chat/${trackedTopic._id}`
                                            }
                                            style={{cursor: 'pointer'}}
                                        >
                                            <h3 className="text-lg font-medium text-gray-900">
                                                {trackedTopic.topic
                                                    ? trackedTopic.topic
                                                          .charAt(0)
                                                          .toUpperCase() +
                                                      trackedTopic.topic.slice(1)
                                                    : ""}
                                            </h3>
                                        </div>

                                        <button
                                            className="absolute top-0 right-0 p-2 text-gray-500 hover:text-red-500 transition-colors duration-300 ease-in-out"
                                            onClick={() => {
                                                deleteTrackedTopic(
                                                    trackedTopic._id,
                                                    trackedTopic.isPinnedTopic
                                                );
                                            }}
                                            title="Delete tracked topic"
                                        >
                                            <FontAwesomeIcon icon={faTrash} />
                                        </button>
                                    </div>
                                ))}
                            <TrackTopicButton getTopics={getTopics} />
                        </div>
                        <h2 className="text-2xl font-bold text-center">
                            Headlines Today
                        </h2>
                        <h3
                            className="text-lg font-medium text-gray-700 text-center mb-8"
                            id="topics-grid"
                        >
                            {new Date().toLocaleDateString("en-US", {
                                year: "numeric",
                                month: "long",
                                day: "numeric",
                            })}
                        </h3>
                        {isLoadingHeadlines && (
                            <div className="flex justify-center items-center mt-4">
                                <p className="mr-4 text-lg">Loading </p>
                                <Ring color="#6d28d9" />
                            </div>
                        )}
                        {!isLoadingHeadlines && (
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mt-4">
                                {newsTopics
                                    .filter(
                                        (newsTopic) =>
                                            newsTopic.topic &&
                                            !(
                                                newsTopic.isTrackedTopic ||
                                                newsTopic.isPinnedTopic
                                            )
                                    )
                                    .map((newsTopic) => (
                                        <div
                                            key={newsTopic._id}
                                            className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 ease-in-out relative"
                                        >
                                            <a
                                                href={`/topic/${newsTopic._id}`}
                                                className="block p-4 pt-6"
                                            >
                                                <h3 className="text-lg font-medium text-gray-900">
                                                    {newsTopic.topic
                                                        ? newsTopic.topic
                                                              .charAt(0)
                                                              .toUpperCase() +
                                                          newsTopic.topic.slice(1)
                                                        : ""}
                                                </h3>
                                            </a>

                                            <button
                                                className="absolute top-0 right-0 p-2 text-gray-500 hover:text-purple-800 transition-colors duration-300 ease-in-out"
                                                onClick={() => {
                                                    setPinnedTopic(newsTopic._id);
                                                }}
                                                title="Track this topic"
                                            >
                                                <FontAwesomeIcon
                                                    icon={faThumbtack}
                                                    transform={{ rotate: 45 }}
                                                />
                                            </button>
                                        </div>
                                    ))}
                            </div>
                        )}
                    </div>
                    <div className="w-full">
                        <p> chat?? </p>
                        <ChatCopy
                          currentArticle={urlID}
                        />
                      </div>
                      <p> chat?? </p>
                </div>
            </div>
        </>
    );
};

export default Index;
