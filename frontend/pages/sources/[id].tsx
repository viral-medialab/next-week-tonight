import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { ArticleType } from "@/components/ArticlesGrid";
import SourceChart from "@/components/SourceChart";
import SourceSidebar from "@/components/SourceSidebar";
import { Ring } from "@uiball/loaders";

const Facts = () => {
    const router = useRouter();
    const { id } = router.query;
    const [newsTopic, setNewsTopic] = useState<any>({});
    const [selectedArticleId, setSelectedArticleId] = useState<any>(null);
    const [pinnedArticleId, setPinnedArticleId] = useState<any>(null);
    const [sources, setSources] = useState<any>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        //getting topic from backend with id
        fetch("/api/getNewsByTopicId", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ topicId: id }),
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error("404 Sources Not Found");
                }
                return res.json();
            })
            .then((data) => {
                console.log(data);
                //get only first 4 articles
                // setNewsTopic({ ...data, articles: data.articles.slice(0, 4) });
                setNewsTopic(data);
                //get sources of these articles
                fetch(`/api/getSourcesAndTone`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        topicsAndArticles: data,
                    }),
                }).then((res) => {
                    if (!res.ok) {
                        throw new Error("404 Sources Not Found");
                    }
                    res.json().then((data) => {
                        console.log(data);
                        setSources(data);
                        setIsLoading(false);
                    });
                });
            })
            .catch((err) => {
                console.log(err);
                setIsLoading(true);
            });
    }, [id]);

    const onPinArticle = () => {
        if (!pinnedArticleId) {
            setPinnedArticleId(selectedArticleId);
        } else {
            setPinnedArticleId(null);
        }
    };

    return (
        <>
            {isLoading && (
                <div className="container w-full mx-auto px-4 py-8 flex h-full">
                    <div className="w-full h-full flex flex-col justify-center items-center">
                        <Ring color="#6366F1" />
                        <p className="mr-4 mt-2 text-lg">
                            Still processing this topic. Check back later{" "}
                        </p>
                    </div>
                </div>
            )}

            {!isLoading && (selectedArticleId || pinnedArticleId) && (
                <SourceSidebar
                    articleToShow={sources.sourceInfo.find(
                        (article: any) => article._id === selectedArticleId
                    )}
                    pinnedArticle={sources.sourceInfo.find(
                        (article: any) => article._id === pinnedArticleId
                    )}
                    onPinArticle={onPinArticle}
                    topicId={sources._id}
                    topicName={sources.topic}
                />
            )}
            {!isLoading && (
                <div className="container mx-auto px-4 py-8 flex flex-col h-full ">
                    <div className="w-full flex flex-col justify-around pr-4">
                        <h1 className="text-4xl text-center font-bold mr-2 mb-4">
                            {newsTopic.topic
                                ? newsTopic.topic.charAt(0).toUpperCase() +
                                  newsTopic.topic.slice(1)
                                : ""}
                        </h1>
                        <p className="text-lg text-center mr-2 mb-8">
                            Click on a source to see more details
                            <br /> Scroll to zoom and click and drag to pan
                        </p>

                        {/* {selectedArticleId && (
                        <h2 className="text-xl font-bold mb-8">
                            {selectedArticleId}
                        </h2>
                    )} */}
                    </div>
                    <div className="w-full h-full">
                        <SourceChart
                            sources={sources}
                            setSelectedArticleId={setSelectedArticleId}
                            isLoading={isLoading}
                        />
                    </div>
                </div>
            )}
        </>
    );
};

export default Facts;
