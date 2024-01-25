import { faMapPin, faMinus, faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Disclosure } from "@headlessui/react";
import { useEffect, useState } from "react";

type SourceCardComparisonProps = {
    articleOne: any;
    articleTwo: any;
    topicId: string;
    topicName: string;
};
const SourceCardComparison = ({
    articleOne,
    articleTwo,
    topicId,
    topicName,
}: SourceCardComparisonProps) => {
    const [sourceComparison, setSourceComparison] = useState<any>(null);

    console.log(
        "articleOneId",
        articleOne._id,
        "articleTwoId",
        articleTwo._id,
        "topicId",
        topicId,
        "topicName",
        topicName
    );
    useEffect(() => {
        fetch(`/api/getSourceComparison`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                articleOne: articleOne,
                articleTwo: articleTwo,
                topicId: topicId,
                topicName: topicName,
            }),
        }).then((res) => {
            res.json().then((data) => {
                console.log("sourceCardComparison result", data);
                setSourceComparison(data);
            });
        });
    }, [articleOne, articleTwo, topicId, topicName]);

    if (!sourceComparison) return <p>Retrieving comparisons...</p>;
    else if (sourceComparison.sameTopic === undefined)
        return <p>Error in comparing the two articles, try others</p>;
    else if (sourceComparison.sameTopic === false)
        return <p>The two articles are not speaking of the same topic</p>;
    return (
        <>
            <h3 className="text-xl font-bold mb-4">
                Comparison between the two articles
            </h3>
            <Disclosure>
                {({ open }) => (
                    <>
                        <Disclosure.Button className="flex w-full justify-between rounded-lg bg-sky-500 mb-4  text-left text-lg font-medium hover:bg-sky-700 focus:outline-none ">
                            <span>Similarities in Material</span>
                            <FontAwesomeIcon
                                icon={open ? faMinus : faPlus}
                                className="h-6 w-6 "
                            />
                        </Disclosure.Button>
                        <Disclosure.Panel className="pb-4">
                            <ul>
                                {sourceComparison.overlappingMaterial.map(
                                    (overlap: any, index: number) => (
                                        <li key={index} className="mb-2">
                                            {overlap}
                                        </li>
                                    )
                                )}
                            </ul>
                        </Disclosure.Panel>
                    </>
                )}
            </Disclosure>
            <Disclosure>
                {({ open }) => (
                    <>
                        <Disclosure.Button className="flex w-full justify-between rounded-lg bg-sky-500 mb-4  text-left text-lg font-medium hover:bg-sky-700 focus:outline-none ">
                            <span>Differences in Material</span>
                            <FontAwesomeIcon
                                icon={open ? faMinus : faPlus}
                                className="h-6 w-6 "
                            />
                        </Disclosure.Button>
                        <Disclosure.Panel className="pb-4">
                            <ul>
                                {sourceComparison.differences.map(
                                    (difference: any, index: number) => (
                                        <li key={index} className="mb-2">
                                            {difference}
                                        </li>
                                    )
                                )}
                            </ul>
                        </Disclosure.Panel>
                    </>
                )}
            </Disclosure>
        </>
    );
};
export default SourceCardComparison;
