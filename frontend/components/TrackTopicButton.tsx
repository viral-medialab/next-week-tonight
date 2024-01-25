import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { usePopper } from "react-popper";
import { Popover, Transition } from "@headlessui/react";
import { Fragment, useEffect, useRef, useState } from "react";

type TrackTopicButtonProps = {
    getTopics: () => void;
};
export default function TrackTopicButton({ getTopics }: TrackTopicButtonProps) {
    let [referenceElement, setReferenceElement] = useState();

    let [popperElement, setPopperElement] = useState();
    let { styles, attributes } = usePopper(referenceElement, popperElement, {
        placement: "right",
        modifiers: [
            {
                name: "flip",
            },
            {
                name: "preventOverflow",
            },
            {
                name: "offset",
                options: {
                    offset: [0, -10],
                },
            },
        ],
    });

    const inputRef = useRef<HTMLInputElement>(null);
    const [topicToAdd, setTopicToAdd] = useState<string>("");
    const [isAddingTopicToDB, setIsAddingTopicToDB] = useState<boolean>(false);

    useEffect(() => {
        inputRef.current?.focus();
        console.log("focused input");
    }, [inputRef.current]);

    const handleAddTopic = (closePopover: () => void) => {
        const today = new Date();
        const date =
            today.getFullYear() +
            "-" +
            (today.getMonth() + 1) +
            "-" +
            today.getDate();
        if (!topicToAdd.trim()) return;
        setIsAddingTopicToDB(true);
        const trackedTopic = {
            _id: undefined,
            topic: topicToAdd.trim(),
            isArticlesProcessed: false,
            date: date, // date in format yyyy-mm-dd
            createdAt: new Date(),
            isTrackedTopic: true,
        };

        fetch("/api/addTrackedTopic", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ trackedTopic }),
        }).then((res) => {
            res.json().then((data) => {
                console.log(data);
                setIsAddingTopicToDB(false);
                setTopicToAdd("");
                getTopics();
                closePopover();
            });
        });
    };

    return (
        <div className=" flex flex-col justify-center items-center text-center items-center bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 py-8 px-10 ease-in-out cursor-pointer">
            <Popover className="relative">
                {({ open }) => (
                    <>
                        <Popover.Button ref={setReferenceElement as any}>
                            Add new tracked topic
                            <FontAwesomeIcon
                                icon={faPlus}
                                size="lg"
                                className="h-12 w-12 text-gray-400 pt-2"
                            />
                        </Popover.Button>
                        <Transition
                            as={Fragment}
                            enter="transition ease-out duration-200"
                            enterFrom="opacity-0 translate-y-1"
                            enterTo="opacity-100 translate-y-0"
                            leave="transition ease-in duration-150"
                            leaveFrom="opacity-100 translate-y-0"
                            leaveTo="opacity-0 translate-y-1"
                        >
                            <Popover.Panel
                                className="absolute left-1/2 z-10 mt-3 w-screen max-w-sm -translate-x-1/2 transform px-4 sm:px-0 lg:max-w-lg"
                                ref={setPopperElement as any}
                                style={styles.popper}
                                {...attributes.popper}
                            >
                                {({ close }) => (
                                    <div className="flex overflow-hidden rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 w-full px-2 py-4">
                                        <input
                                            type="text"
                                            id="topic"
                                            name="topic"
                                            value={topicToAdd}
                                            onChange={(e) =>
                                                setTopicToAdd(e.target.value)
                                            }
                                            onKeyDown={(e) => {
                                                if (
                                                    e.key === "Enter" &&
                                                    !isAddingTopicToDB
                                                ) {
                                                    handleAddTopic(close);

                                                    // exit the popover by hitting escape
                                                }
                                            }}
                                            className="shadow-sm focus:ring-orange-500 focus:border-orange-500 block w-full sm:text-sm border-gray-300 rounded-md px-3 py-2"
                                            placeholder="Enter a topic to track"
                                            ref={inputRef}
                                        />

                                        <button
                                            type="button"
                                            onClick={() =>
                                                handleAddTopic(close)
                                            }
                                            className={
                                                "inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-orange-700 text-base font-medium text-white hover:bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 sm:text-sm w-14 h-full ml-2" +
                                                (isAddingTopicToDB
                                                    ? " cursor-not-allowed opacity-50"
                                                    : "")
                                            }
                                        >
                                            {!isAddingTopicToDB
                                                ? "Add"
                                                : "Adding"}
                                        </button>
                                    </div>
                                )}
                            </Popover.Panel>
                        </Transition>
                    </>
                )}
            </Popover>
        </div>
    );
}

function IconOne() {
    return (
        <svg
            width="48"
            height="48"
            viewBox="0 0 48 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
        >
            <rect width="48" height="48" rx="8" fill="#FFEDD5" />
            <path
                d="M24 11L35.2583 17.5V30.5L24 37L12.7417 30.5V17.5L24 11Z"
                stroke="#FB923C"
                strokeWidth="2"
            />
            <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M16.7417 19.8094V28.1906L24 32.3812L31.2584 28.1906V19.8094L24 15.6188L16.7417 19.8094Z"
                stroke="#FDBA74"
                strokeWidth="2"
            />
            <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M20.7417 22.1196V25.882L24 27.7632L27.2584 25.882V22.1196L24 20.2384L20.7417 22.1196Z"
                stroke="#FDBA74"
                strokeWidth="2"
            />
        </svg>
    );
}

function IconTwo() {
    return (
        <svg
            width="48"
            height="48"
            viewBox="0 0 48 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
        >
            <rect width="48" height="48" rx="8" fill="#FFEDD5" />
            <path
                d="M28.0413 20L23.9998 13L19.9585 20M32.0828 27.0001L36.1242 34H28.0415M19.9585 34H11.8755L15.9171 27"
                stroke="#FB923C"
                strokeWidth="2"
            />
            <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M18.804 30H29.1963L24.0001 21L18.804 30Z"
                stroke="#FDBA74"
                strokeWidth="2"
            />
        </svg>
    );
}

function IconThree() {
    return (
        <svg
            width="48"
            height="48"
            viewBox="0 0 48 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
        >
            <rect width="48" height="48" rx="8" fill="#FFEDD5" />
            <rect x="13" y="32" width="2" height="4" fill="#FDBA74" />
            <rect x="17" y="28" width="2" height="8" fill="#FDBA74" />
            <rect x="21" y="24" width="2" height="12" fill="#FDBA74" />
            <rect x="25" y="20" width="2" height="16" fill="#FDBA74" />
            <rect x="29" y="16" width="2" height="20" fill="#FB923C" />
            <rect x="33" y="12" width="2" height="24" fill="#FB923C" />
        </svg>
    );
}
