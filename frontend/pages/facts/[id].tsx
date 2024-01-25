import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Article from "@/components/Article";
import ArticlesGrid, { ArticleType } from "@/components/ArticlesGrid";
import Chat from "@/components/Chat";
import binarySearch from "@/utils/binarySearch";
import Link from "next/link";
import HeaderTopic from "@/components/HeaderTopic";
import { Ring } from "@uiball/loaders";

interface Props {
    newsTopic: {
        articles: ArticleType[];
    };
    handleArticleClick: (article: ArticleType) => void;
}

const Facts = () => {
    const router = useRouter();
    const { id } = router.query;
    const [newsTopic, setNewsTopic] = useState<any>({});
    const [selectedArticle, setSelectedArticle] = useState<any>(null);
    const [highlightedText, setHighlightedText] = useState<any>("");
    const [currentArticle, setCurrentArticle] = useState<any>(null);
    const [allFacts, setAllFacts] = useState<any>(null);
    const [sortBy, setSortBy] = useState<string>("");
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
                    throw new Error("404 Facts Not Found");
                }
                return res.json();
            })
            .then((data) => {
                console.log(data);
                //get only first 4 articles
                // setNewsTopic({ ...data, articles: data.articles.slice(0, 4) });
                setNewsTopic(data);
                //get facts of these articles from /api/getFacts
                fetch(`/api/getFacts`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        topicId: id,
                    }),
                })
                    .then((res) => {
                        if (!res.ok) {
                            throw new Error("404 Facts Not Found");
                        }
                        return res.json();
                    })
                    .then((data) => {
                        console.log(data);
                        setAllFacts(data);
                        setIsLoading(false);
                    })
                    .catch((err) => {
                        console.log(err);
                        setIsLoading(true);
                    });
            })
            .catch((err) => {
                console.log(err);
                setIsLoading(true);
            });
    }, [id]);

    useEffect(() => {
        const element = document.getElementById("highlighted-text");
        if (element) {
            element.scrollIntoView({ behavior: "smooth" });
        }
    }, [highlightedText]);

    const handleSourceClick = (id: string) => {
        console.log(id);
        setCurrentArticle(
            newsTopic.articles.find((article: any) => article._id === id)
        );
    };

    const handleSortBy = (sortBy: string) => {
        setSortBy(sortBy);
    };
    const sortFacts = (facts: any[]) => {
        if (sortBy === "By number of sources") {
            return facts.sort(
                (a: any, b: any) => b.sources.length - a.sources.length
            );
        } else if (sortBy === "By latest") {
            return facts.sort((a: any, b: any) => {
                const aLatestDate = new Date(
                    Math.max(
                        ...a.sources.map((source: any) =>
                            new Date(
                                newsTopic.articles.find(
                                    (article: any) =>
                                        article._id === source.articleId
                                ).datePublished
                            ).getTime()
                        )
                    )
                );
                const bLatestDate = new Date(
                    Math.max(
                        ...b.sources.map((source: any) =>
                            new Date(
                                newsTopic.articles.find(
                                    (article: any) =>
                                        article._id === source.articleId
                                ).datePublished
                            ).getTime()
                        )
                    )
                );
                return bLatestDate.getTime() - aLatestDate.getTime();
            });
        } else {
            return facts.sort((a: any, b: any) =>
                a.claim.localeCompare(b.claim)
            );
        }
    };

    const highlightText = (search: any, text: any) => {
        //make search case insensitive
        search = search.toLowerCase();
        const lowerText = text.toLowerCase();
        const searchWords = search
            .split(" ")
            .map((word: string) => {
                return word.replace(/^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$/g, "");
            })
            .filter((word: string) => word.trim().length > 0);
        const allIndices = [];
        for (let i = 0; i < searchWords.length; i++) {
            //get all indices of searchWords[i] in lowerText
            const indices = [];
            let idx = lowerText.indexOf(searchWords[i]);
            while (idx !== -1) {
                indices.push([idx, idx + searchWords[i].length]);
                idx = lowerText.indexOf(searchWords[i], idx + 1);
            }
            allIndices.push(indices);
            // console.log("searchWords[i]", searchWords[i], "indices", indices);
        }

        const candidates = allIndices[0];
        console.log("candidates before", candidates);
        for (let i = 1; i < allIndices.length; i++) {
            const newCandidates = [];
            for (let j = 0; j < candidates.length; j++) {
                const candidate = candidates[j];
                const haystack = allIndices[i].map((x) => x[0]);
                const lowerBound = binarySearch(
                    haystack,
                    candidate[1],
                    (a, b) => a - b,
                    -1,
                    -1,
                    true,
                    false
                );
                // console.log(
                //     "candidate",
                //     candidate,
                //     "lowerBound",
                //     lowerBound,
                //     "allIndices[i]",
                //     allIndices[i]
                // );
                if (lowerBound === haystack.length) {
                    //infinity
                    candidates[j][1] = Infinity;
                } else {
                    const result = allIndices[i][lowerBound][1];
                    candidates[j][1] = result;
                }
            }
        }

        const finalCandidates = candidates.reduce((acc, curr) => {
            if (curr[1] - curr[0] < acc[1] - acc[0]) {
                return curr;
            }
            return acc;
        }, candidates[0]);
        console.log("candidates after", finalCandidates);
        const extractedText = text.substring(
            finalCandidates[0],
            finalCandidates[1]
        );
        const highlightedText = text.replace(
            extractedText,
            `<span class="bg-yellow-200" id="highlighted-text">${extractedText}</span>`
        );

        return highlightedText;
    };

    const handleArticleClick = (article: any, source: any) => {
        setSelectedArticle(article);
        setHighlightedText("");
        if (article) {
            console.log("article", article, "source", source.citation);
            console.log("length of citation", source.citation.length);

            const highlighted = highlightText(source.citation, article.content);

            // article.content.replace(
            //     source.citation,
            //     `<span class="bg-yellow-200" id="highlighted-text">${source.citation}</span>`
            // );
            setHighlightedText(highlighted);

            const element = document.getElementById("highlighted-text");
            if (element) {
                element.scrollIntoView({ behavior: "smooth" });
            }
        } else {
            setHighlightedText("");
            setSelectedArticle(null);
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

            {!isLoading && (
                <div className="container w-full mx-auto px-4 py-8 flex h-full">
                    <div
                        className={`${
                            selectedArticle ? "w-8/12" : "w-full"
                        } pr-4 overflow-y-auto h-full`}
                    >
                        <h1 className="text-4xl text-center font-bold mb-12">
                            {newsTopic.topic
                                ? newsTopic.topic.charAt(0).toUpperCase() +
                                  newsTopic.topic.slice(1)
                                : ""}
                        </h1>
                        <div className="flex justify-center mb-10">
                            <button
                                className={`${
                                    sortBy === ""
                                        ? "bg-gray-400 text-gray-900"
                                        : "bg-gray-200 text-gray-700"
                                } px-4 py-2 rounded-l-lg`}
                                onClick={() => handleSortBy("")}
                            >
                                No filter
                            </button>
                            <button
                                className={`${
                                    sortBy === "By number of sources"
                                        ? "bg-gray-400 text-gray-900"
                                        : "bg-gray-200 text-gray-700"
                                } px-4 py-2 border-l border-r`}
                                onClick={() =>
                                    handleSortBy("By number of sources")
                                }
                            >
                                By number of sources
                            </button>
                            <button
                                className={`${
                                    sortBy === "By latest"
                                        ? "bg-gray-400 text-gray-900"
                                        : "bg-gray-200 text-gray-700"
                                } px-4 py-2 rounded-r-lg`}
                                onClick={() => handleSortBy("By latest")}
                            >
                                By latest
                            </button>
                        </div>
                        {allFacts && (
                            <table className="table-auto">
                                <thead>
                                    <tr>
                                        <th className="px-4 py-2">Claim</th>
                                        <th className="px-4 py-2">
                                            Sources (click on a source to see
                                            citation)
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sortFacts(allFacts.facts).map(
                                        (fact: any, index: number) => (
                                            <tr key={index}>
                                                <td className="border px-4 py-2">
                                                    {fact.claim}
                                                </td>
                                                <td className="border px-4 py-2">
                                                    {fact.sources.map(
                                                        (
                                                            source: any,
                                                            index: number
                                                        ) => (
                                                            <span
                                                                key={index}
                                                                className="inline-block bg-gray-200 rounded-full px-3 py-1 text-sm font-medium  mr-2 cursor-pointer"
                                                                onClick={() =>
                                                                    handleArticleClick(
                                                                        newsTopic.articles.find(
                                                                            (
                                                                                article: any
                                                                            ) =>
                                                                                article._id ===
                                                                                source.articleId
                                                                        ),
                                                                        source
                                                                    )
                                                                }
                                                            >
                                                                {newsTopic.articles
                                                                    .find(
                                                                        (
                                                                            article: any
                                                                        ) =>
                                                                            article._id ===
                                                                            source.articleId
                                                                    )
                                                                    ?.provider[0].name.replace(
                                                                        "on MSN.com",
                                                                        ""
                                                                    )}
                                                            </span>
                                                        )
                                                    )}
                                                </td>
                                            </tr>
                                        )
                                    )}
                                </tbody>
                            </table>
                        )}
                    </div>
                    {selectedArticle && (
                        <div className="w-full h-full overflow-y-auto">
                            <div className="bg-white rounded-lg shadow-lg p-8">
                                <button
                                    onClick={() => setSelectedArticle(null)}
                                    className="text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700 float-right"
                                >
                                    <span className="text-blue-700">
                                        Close article
                                    </span>
                                </button>

                                <h2 className="text-2xl font-bold mb-4">
                                    {selectedArticle.name}
                                </h2>
                                <p className="text-gray-500">
                                    Source:{" "}
                                    {selectedArticle.provider[0].name.replace(
                                        "on MSN.com",
                                        ""
                                    )}
                                </p>
                                <p className="text-gray-500 mb-4">
                                    By Fox Knight
                                </p>
                                <article
                                    className="prose lg:prose-xl"
                                    dangerouslySetInnerHTML={{
                                        __html: highlightedText,
                                    }}
                                />
                            </div>
                        </div>
                    )}
                </div>
            )}
        </>
    );
};
export default Facts;
