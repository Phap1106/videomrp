
"use client";

import * as React from "react";
import clsx from "clsx";

interface SliderProps extends React.InputHTMLAttributes<HTMLInputElement> {
    className?: string;
}

export const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
    ({ className, ...props }, ref) => {
        return (
            <input
                type="range"
                ref={ref}
                className={clsx(
                    "w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-cyan-500/50",
                    className
                )}
                {...props}
            />
        );
    }
);
Slider.displayName = "Slider";
