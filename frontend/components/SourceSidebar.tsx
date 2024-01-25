import { faMapPin, faMinus, faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Disclosure } from "@headlessui/react";
import SourceCardDetails from "./SourceCardDetails";
import { useState } from "react";
import SourceCardComparison from "./SourceCardComparison";
import { on } from "events";

type SourceSidebarProps = {
    articleToShow: any;
    pinnedArticle: any;
    onPinArticle: () => void;
    topicId: string;
    topicName: string;
};

const SourceSidebar = ({
    articleToShow,
    pinnedArticle,
    onPinArticle,
    topicId,
    topicName,
}: SourceSidebarProps) => {
    const [isSourceComparison, setIsSourceComparison] =
        useState<boolean>(false); // true if we are comparing two articles

    return (
        <div className="absolute top-20 left-0 w-3/12 h-full bg-white border-black shadow-2xl p-4 z-50 overflow-y-auto">
            {pinnedArticle && (
                <div className=" w-full bg-gray-300 rounded-lg shadow-lg p-6 mb-4">
                    <div className="flex flex-col">
                        <SourceCardDetails articleToShow={pinnedArticle} />
                        <button
                            onClick={() => {
                                onPinArticle();
                                setIsSourceComparison(false);
                            }}
                            className="bg-gray-400 border border-black rounded-full p-2 hover:bg-gray-500"
                        >
                            {pinnedArticle
                                ? "Unpin article"
                                : "Pin article to compare"}{" "}
                            <FontAwesomeIcon
                                icon={faMapPin}
                                className={
                                    "h-4 w-4 " +
                                    (pinnedArticle ? "rotate-45" : "")
                                }
                            />
                        </button>
                    </div>
                </div>
            )}

            {articleToShow &&
                (!pinnedArticle || articleToShow._id !== pinnedArticle._id) && (
                    <div className=" w-full bg-gray-300 rounded-lg shadow-lg p-6 mb-4">
                        <div className="flex flex-col">
                            <SourceCardDetails articleToShow={articleToShow} />
                            {!pinnedArticle ? (
                                <button
                                    onClick={onPinArticle}
                                    className="bg-gray-400 border border-black rounded-full p-2 hover:bg-gray-500"
                                >
                                    {pinnedArticle
                                        ? "Unpin article"
                                        : "Pin article to compare"}{" "}
                                    <FontAwesomeIcon
                                        icon={faMapPin}
                                        className={
                                            "h-4 w-4 " +
                                            (pinnedArticle ? "rotate-45" : "")
                                        }
                                    />
                                </button>
                            ) : (
                                <button
                                    onClick={() =>
                                        setIsSourceComparison(
                                            !isSourceComparison
                                        )
                                    }
                                    className="bg-gray-400 border border-black rounded-full p-2 hover:bg-gray-500"
                                >
                                    {isSourceComparison
                                        ? "Stop comparing with this article"
                                        : "Compare with this article"}
                                </button>
                            )}
                        </div>
                    </div>
                )}
            {isSourceComparison && (
                <div className=" w-full bg-gray-300 rounded-lg shadow-lg p-6 mb-4">
                    <SourceCardComparison
                        articleOne={pinnedArticle}
                        articleTwo={articleToShow}
                        topicId={topicId}
                        topicName={topicName}
                    />
                </div>
            )}
        </div>
    );
};
export default SourceSidebar;
