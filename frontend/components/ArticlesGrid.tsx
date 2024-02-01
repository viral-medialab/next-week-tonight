import React, { useState, useEffect } from "react";

export interface ArticleType {
    _id: string;
    name: string;
    url: string;
    image?: {
        thumbnail: {
            contentUrl: string;
            width: number;
            height: number;
        };
    };
    description: string;
    about: {
        readLink: string;
        name: string;
    }[];
    mentions: {
        name: string;
    }[];
    provider: {
        _type: string;
        name: string;
        image?: {
            thumbnail: {
                contentUrl: string;
            };
        };
    }[];
    datePublished: string;
    video?: {
        name: string;
        motionThumbnailUrl: string;
        thumbnail: {
            width: number;
            height: number;
        };
    };
    category: string;
    content: string;
}

interface Props {
    newsTopic: {
        articles: ArticleType[];
    };
    handleArticleClick: (article: ArticleType) => void;
}

export default function ArticlesGrid({ newsTopic, handleArticleClick }: Props) {

    const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

    const uniqueProviders = Array.from(new Set(newsTopic.articles?.map(article => article.publisher)));

    console.log("Unique Providers:", uniqueProviders);

    const handleProviderChange = (provider: string | null) => {
        setSelectedProvider(provider);
    };

    const filteredArticles = newsTopic.articles?.filter(article => selectedProvider === null || selectedProvider === "" || article.publisher === selectedProvider);

    console.log(filteredArticles);

    const [fetchedArticleNames, setFetchedArticleNames] = useState<string[]>([]);

    useEffect(() => {
        // Fetch names for all articles
        const fetchArticleNames = async () => {
          const namesPromises = newsTopic.articles?.map(async (article) => {
            try {
              const response = await fetch(
                "http://127.0.0.1:5000/api/gather_article_info",
                {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({
                    articleUrl: article.url,
                  }),
                }
              );

              if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
              }

              const data = await response.json();
              return data["title"];
            } catch (error) {
              console.error("Error fetching article name:", error);
              return "";
            }
          });

          const names = await Promise.all(namesPromises);
          setFetchedArticleNames(names);
        };

        fetchArticleNames();
      }, [newsTopic.articles]);

    return (
        <div className="w-full">
            <div className="mb-4">
                <label htmlFor="providerDropdown" className="mr-2 text-gray-700">Pick Your News Source:</label>
                <select
                    id="providerDropdown"
                    onChange={(e) => handleProviderChange(e.target.value)}
                    value={selectedProvider || ''}
                    className="p-2 border rounded"
                >
                    <option value="">All Providers</option>
                    {uniqueProviders.map((provider, index) => (
                        <option key={index} value={provider}>{provider}</option>
                    ))}
                </select>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-1 lg:grid-cols-3 gap-8 w-full">
                {filteredArticles?.map((article: ArticleType, index) => (
                    <div
                        key={article._id}
                        className="bg-white rounded-lg shadow-lg overflow-hidden"
                        // onClick={() => handleArticleClick(article)}
                    >
                    <a
                        href={`/article/${article.id}`}
                    >
                        {article.image.thumbnail && (
                            <img
                                src={article.image.thumbnail.contentUrl.replace(
                                    /&pid=.*$/,
                                    ""
                                )}
                                alt={article.name}
                                className="w-full h-48 object-cover"
                            />
                        )}
                        <div className="p-6">
                            <div className="flex items-center mt-4 mb-2">
                                <p className="text-gray-700 text-sm">
                                    {article.publisher}
                                </p>
                            </div>
                            <h2 className="text-2xl font-bold mb-2">
                                {fetchedArticleNames[index] || article.name}
                            </h2>
                            {/*<p className="text-gray-700 text-base">
                                {article.description}
                            </p>*/}
                            <button
                                onClick={() => handleArticleClick(article)}
                                className="text-blue-500 font-bold hover:text-blue-700 mt-4"
                            >
                                Read more
                            </button>
                        </div>
                      </a>
                    </div>
                ))}
            </div>
        </div>
    );
}