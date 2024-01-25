import { faMapPin, faMinus, faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Disclosure } from "@headlessui/react";

type SourceCardDetailsProps = {
    articleToShow: any;
};
const SourceCardDetails = ({ articleToShow }: SourceCardDetailsProps) => {
    return (
        <>
            <h3 className="text-xl font-bold mb-4">{articleToShow.name}</h3>
            <h3 className="text-lg font-medium ">Publisher</h3>
            <p className="pl-2 mb-4">
                {" "}
                {articleToShow.provider[0].name.replace("on MSN.com", "")}
            </p>
            <h3 className="text-lg font-medium ">Date Published</h3>
            <p className="pl-2 mb-4">
                {new Date(articleToShow.datePublished).toLocaleDateString()}
            </p>
            <h3 className="text-lg font-medium ">Author</h3>
            <p className="pl-2 mb-4">Hero of knights</p>

            <h3 className="text-lg font-medium ">Tone</h3>
            <p className="pl-2 mb-4"> {articleToShow.tone}</p>

            <Disclosure>
                {({ open }) => (
                    <>
                        <Disclosure.Button className="flex w-full justify-between rounded-lg bg-sky-500 mb-4 text-left text-lg font-medium hover:bg-sky-700 focus:outline-none ">
                            <span>Description</span>
                            <FontAwesomeIcon
                                icon={open ? faMinus : faPlus}
                                className="h-6 w-6 "
                            />
                        </Disclosure.Button>
                        <Disclosure.Panel className="pb-4">
                            <p>
                                {articleToShow.description.replace(
                                    /(.+?[\w\s])\W*$/,
                                    "$1..."
                                )}
                            </p>
                        </Disclosure.Panel>
                    </>
                )}
            </Disclosure>
            <Disclosure>
                {({ open }) => (
                    <>
                        <Disclosure.Button className="flex w-full justify-between rounded-lg bg-sky-500 mb-4  text-left text-lg font-medium hover:bg-sky-700 focus:outline-none ">
                            <span>Sources Cited</span>
                            <FontAwesomeIcon
                                icon={open ? faMinus : faPlus}
                                className="h-6 w-6 "
                            />
                        </Disclosure.Button>
                        <Disclosure.Panel className="pb-4">
                            <ul>
                                {articleToShow.sourcesCited.map(
                                    (source: any, index: number) => (
                                        <li key={index} className="pl-2">
                                            {source}
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
export default SourceCardDetails;
