"use client";
import { Recovery } from "@/components/recovery";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return <Recovery locale="en" reset={reset} />;
}
