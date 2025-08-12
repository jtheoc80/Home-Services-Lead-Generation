import Link from "next/link";

export default function EmptyState({ title, subtitle, ctaLabel, ctaHref }:{
  title:string; subtitle:string; ctaLabel:string; ctaHref:string;
}) {
  return (
    <div className="mx-auto max-w-xl text-center py-24">
      <div className="mx-auto h-16 w-16 rounded-full bg-indigo-50 flex items-center justify-center">🔎</div>
      <h3 className="mt-6 text-2xl font-semibold">{title}</h3>
      <p className="mt-2 text-gray-600">{subtitle}</p>
      <Link href={ctaHref} className="mt-6 inline-block rounded-md bg-indigo-600 px-5 py-2.5 text-white font-semibold hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
        {ctaLabel}
      </Link>
    </div>
  );
}