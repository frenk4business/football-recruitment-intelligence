import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Site } from "@/components/site";
import { copy, sections, type Section } from "@/lib/content";
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
  return { title: copy.en.nav[section as Section] ?? "Research" };
}
export default async function Page({
  params,
}: {
  params: Promise<{ section: string }>;
}) {
  const { section } = await params;
  if (!sections.includes(section as Section) || section === "home") notFound();
  return <Site locale="en" section={section as Section} />;
}
