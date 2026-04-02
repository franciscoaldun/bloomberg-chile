"use client";

import { useEffect, useRef, useState } from "react";

interface FlashCellProps {
  value: string;
  change: number | null;
  className?: string;
}

export default function FlashCell({ value, change, className = "" }: FlashCellProps) {
  const [flashClass, setFlashClass] = useState("");
  const prevValue = useRef(value);

  useEffect(() => {
    if (prevValue.current !== value) {
      if (change !== null && change > 0) setFlashClass("flash-up");
      else if (change !== null && change < 0) setFlashClass("flash-down");
      prevValue.current = value;

      const timer = setTimeout(() => setFlashClass(""), 600);
      return () => clearTimeout(timer);
    }
  }, [value, change]);

  const colorClass =
    change === null || change === 0
      ? "text-bb-amber"
      : change > 0
        ? "text-bb-green"
        : "text-bb-red";

  return (
    <td className={`${flashClass} ${colorClass} ${className}`}>
      {value}
    </td>
  );
}
