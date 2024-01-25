import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Article from "@/components/Article";
import ArticlesGrid, { ArticleType } from "@/components/ArticlesGrid";
import Chat from "@/components/Chat";
import Link from "next/link";
import HeaderTopic from "@/components/HeaderTopic";
import { Ring } from "@uiball/loaders";

interface Props {
    newsTopic: {
        articles: ArticleType[];
    };
    handleArticleClick: (article: ArticleType) => void;
}

const Topic = () => {
    const router = useRouter();
    const { id } = router.query;
    const [newsTopic, setNewsTopic] = useState<any>({});
    const [selectedArticle, setSelectedArticle] = useState<any>(null);
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
                if (res.status === 404) {
                    setIsLoading(true);
                    throw new Error("Topic not found");
                }
                return res.json();
            })
            .then((data) => {
                console.log(data);
                //get only first 4 articles
                // setNewsTopic({ ...data, articles: data.articles.slice(0, 4) });
                setNewsTopic(data);
                setIsLoading(false);
            })
            .catch((err) => {
                console.log(err);
            });
    }, [id]);

    const handleArticleClick = (article: any) => {
        setSelectedArticle(article);
    };

    const handleArticleClose = () => {
        setSelectedArticle(null);
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
            {!isLoading && (
                <div className="container mx-auto px-4 py-8 flex flex-col h-full overflow-auto">
                  <div className="w-full overflow-y-auto h-full">
                    <h1 className="text-4xl font-bold mb-8">
                      {newsTopic.topic
                        ? newsTopic.topic.charAt(0).toUpperCase() + newsTopic.topic.slice(1)
                        : ""}
                    </h1>

                    {!selectedArticle && (
                      <ArticlesGrid
                        newsTopic={{ articles: newsTopic.articles }}
                        handleArticleClick={handleArticleClick}
                      />
                    )}
                    {selectedArticle && (
                      <>
                        <Article
                          articleTitle={selectedArticle.name}
                          articleContent={selectedArticle.content}
                          articleImage={selectedArticle.image?.thumbnail.contentUrl.replace(
                            /&pid=.*$/,
                            ""
                          )}
                          onClose={handleArticleClose}
                        />
                        <hr className="my-4 border-t-4 border-gray-300" />
                        <div className="w-full overflow-y-auto h-full">
                          <Chat
                            topic={newsTopic.topic}
                            currentArticle={selectedArticle}
                            allArticles={
                              selectedArticle
                                ? newsTopic.articles.filter(
                                    (article: any) => article.name !== selectedArticle.name
                                  )
                                : newsTopic.articles
                            }
                          />
                        </div>
                      </>
                    )}
                  </div>
                </div>
            )}
        </>
    );
};

export default Topic;
