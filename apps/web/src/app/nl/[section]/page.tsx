import { pageMetadata } from "@/lib/metadata";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Site } from "@/components/site";
import { sections, type Section } from "@/lib/content";
export const dynamicParams = false;
export function generateStaticParams() {
  return sections.filter((s) => s !== "home").map((section) => ({ section }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ section: string }>;
}): Promise<Metadata> {
  const { section } = await params;
  return pageMetadata(
    "nl",
    sections.includes(section as Section) ? (section as Section) : "home",
  );
}
export default async function Page({
  params,
}: {
  params: Promise<{ section: string }>;
}) {
  const { section } = await params;
  if (!sections.includes(section as Section) || section === "home") notFound();
  return <Site locale="nl" section={section as Section} />;
}
