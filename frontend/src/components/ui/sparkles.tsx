"use client"

import { useId } from "react"
import Particles from "@tsparticles/react"
import { cn } from "@/lib/utils"

export function SparklesCore({
  id,
  className,
  particleColor = "#ffffff",
  particleDensity = 120,
  minSize = 1,
  maxSize = 3,
  speed = 4,
}: {
  id?: string
  className?: string
  particleColor?: string
  particleDensity?: number
  minSize?: number
  maxSize?: number
  speed?: number
}) {
  const generatedId = useId()

  return (
    <Particles
      id={id || generatedId}
      className={cn("h-full w-full", className)}
      options={{
        fullScreen: { enable: false },
        fpsLimit: 120,
        particles: {
          color: { value: particleColor },
          move: {
            enable: true,
            speed,
            outModes: { default: "out" },
          },
          number: {
            density: { enable: true },
            value: particleDensity,
          },
          opacity: {
            value: { min: 0.1, max: 1 },
            animation: { enable: true, speed: speed, sync: false },
          },
          size: {
            value: { min: minSize, max: maxSize },
          },
        },
        detectRetina: true,
      }}
    />
  )
}
