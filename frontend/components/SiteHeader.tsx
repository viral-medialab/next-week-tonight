import React from "react";
import Image from "next/image";

const date = new Date();
const dateString = date.toLocaleDateString("en-US", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

export default function Header() {
  return (
    <header className="flex flex-row py-2 px-12 w-full font-karrik-regular items-center justify-start ">
      <h1 className="text-xl">
        <span className="font-bold">Liquid News</span>
        <span className="px-4">|</span>
        <span className="">{`${dateString}`}</span>
      </h1>
    </header>
  );
}
