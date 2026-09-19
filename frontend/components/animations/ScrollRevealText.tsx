"use client";

import React, { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";

type CharacterProps = {
  char: string;
  index: number;
  centerIndex: number;
  scrollYProgress: any;
};

function Character({
  char,
  index,
  centerIndex,
  scrollYProgress,
}: CharacterProps) {
  const isSpace = char === " ";
  const distanceFromCenter = index - centerIndex;

  const x = useTransform(
    scrollYProgress,
    [0, 0.5],
    [distanceFromCenter * 45, 0]
  );

  const rotate = useTransform(
    scrollYProgress,
    [0, 0.5],
    [distanceFromCenter * 35, 0]
  );

  const y = useTransform(
    scrollYProgress,
    [0, 0.5],
    [-Math.abs(distanceFromCenter) * 18, 0]
  );

  const scale = useTransform(
    scrollYProgress,
    [0, 0.5],
    [0.75, 1]
  );

  return (
    <motion.span
      className={isSpace ? "inline-block w-3" : "inline-block"}
      style={{
        x,
        y,
        rotate,
        scale,
        transformOrigin: "center",
      }}
    >
      {char}
    </motion.span>
  );
}

export default function ScrollRevealText() {
  const targetRef = useRef<HTMLDivElement | null>(null);

  const { scrollYProgress } = useScroll({
    target: targetRef,
  });

  const text = "AI-powered document    intelligence for clearer financial decisions...";
  const characters = text.split("");
  const centerIndex = Math.floor(characters.length / 2);

  return (
    <section
      ref={targetRef}
      className="relative flex h-[180vh] items-center justify-center overflow-hidden"
    >
      <div className="sticky top-0 flex h-screen w-full items-center justify-center px-6">
        <div
          className="max-w-6xl text-center text-5xl font-bold uppercase tracking-[-0.04em] md:text-7xl lg:text-8xl"
          style={{
            perspective: "500px",
          }}
        >
          {characters.map((char, index) => (
            <Character
              key={`${char}-${index}`}
              char={char}
              index={index}
              centerIndex={centerIndex}
              scrollYProgress={scrollYProgress}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
