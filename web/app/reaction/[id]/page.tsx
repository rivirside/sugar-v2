import Link from "next/link";
import { reactions, compoundMap, reactionMap } from "@/lib/data";
import { EvidenceBadge } from "@/components/evidence-badge";
import { COMPOUND_TYPE_COLORS, formatYield } from "@/lib/utils";
import { ArrowRight } from "lucide-react";

export async function generateStaticParams() {
  return reactions.map((r) => ({ id: r.id }));
}

export default async function ReactionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const reaction = reactionMap.get(id);

  if (!reaction) {
    return (
      <div className="flex h-64 items-center justify-center text-zinc-500">
        Reaction not found: {id}
      </div>
    );
  }

  const substrate = compoundMap.get(reaction.substrates[0]);
  const product = compoundMap.get(reaction.products[0]);

  return (
    <div className="flex flex-1 flex-col px-4 py-6 sm:px-6">
      <div className="mx-auto w-full max-w-4xl">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <Link href="/reactions" className="hover:text-zinc-300">
            Reactions
          </Link>
          <span>/</span>
          <span className="text-zinc-300">{reaction.id}</span>
        </div>

        {/* Header */}
        <div className="mt-4">
          <div className="flex items-center gap-3">
            <Link
              href={`/compound/${reaction.substrates[0]}`}
              className="text-2xl font-bold text-zinc-100 hover:text-white"
            >
              {substrate?.name ?? reaction.substrates[0]}
            </Link>
            <ArrowRight className="h-5 w-5 text-zinc-600" />
            <Link
              href={`/compound/${reaction.products[0]}`}
              className="text-2xl font-bold text-zinc-100 hover:text-white"
            >
              {product?.name ?? reaction.products[0]}
            </Link>
          </div>
          <div className="mt-2 flex items-center gap-3">
            <EvidenceBadge tier={reaction.evidence_tier} />
            <span className="text-sm capitalize text-zinc-400">
              {reaction.reaction_type.replace("_", " ")}
            </span>
            <span className="font-mono text-xs text-zinc-500">
              {reaction.id}
            </span>
          </div>
        </div>

        {/* Details grid */}
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {/* Reaction properties */}
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
            <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Properties
            </h3>
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-zinc-500">Yield</dt>
                <dd className="text-zinc-200">{formatYield(reaction.yield)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-zinc-500">Cost Score</dt>
                <dd className="text-zinc-200">
                  {reaction.cost_score.toFixed(2)}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-zinc-500">Cofactor Burden</dt>
                <dd className="text-zinc-200">{reaction.cofactor_burden}</dd>
              </div>
              {reaction.ec_number && (
                <div className="flex justify-between">
                  <dt className="text-zinc-500">EC Number</dt>
                  <dd className="text-zinc-200">{reaction.ec_number}</dd>
                </div>
              )}
              {reaction.enzyme_name && (
                <div className="flex justify-between">
                  <dt className="text-zinc-500">Enzyme</dt>
                  <dd className="text-zinc-200">{reaction.enzyme_name}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Cofactors */}
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
            <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Cofactors
            </h3>
            {reaction.cofactors && reaction.cofactors.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {reaction.cofactors.map((cf, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-300"
                  >
                    {cf}
                  </span>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-sm text-zinc-500">
                No cofactors required
              </p>
            )}
          </div>
        </div>

        {/* Substrate + Product cards */}
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {substrate && (
            <Link
              href={`/compound/${substrate.id}`}
              className="block rounded-lg border border-zinc-800 bg-zinc-900/60 p-4 transition-colors hover:border-zinc-700"
            >
              <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                Substrate
              </h3>
              <p className="mt-2 text-lg font-semibold text-zinc-200">
                {substrate.name}
              </p>
              <div className="mt-1 flex items-center gap-2 text-xs">
                <span
                  className={`capitalize ${COMPOUND_TYPE_COLORS[substrate.type]}`}
                >
                  {substrate.type.replace("_", " ")}
                </span>
                <span className="text-zinc-500">{substrate.chirality}</span>
                <span className="font-mono text-zinc-500">
                  {substrate.formula}
                </span>
              </div>
            </Link>
          )}

          {product && (
            <Link
              href={`/compound/${product.id}`}
              className="block rounded-lg border border-zinc-800 bg-zinc-900/60 p-4 transition-colors hover:border-zinc-700"
            >
              <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                Product
              </h3>
              <p className="mt-2 text-lg font-semibold text-zinc-200">
                {product.name}
              </p>
              <div className="mt-1 flex items-center gap-2 text-xs">
                <span
                  className={`capitalize ${COMPOUND_TYPE_COLORS[product.type]}`}
                >
                  {product.type.replace("_", " ")}
                </span>
                <span className="text-zinc-500">{product.chirality}</span>
                <span className="font-mono text-zinc-500">
                  {product.formula}
                </span>
              </div>
            </Link>
          )}
        </div>

        {/* Database references */}
        {(reaction.ec_number || reaction.rhea_id || (reaction.pmid && reaction.pmid.length > 0) || (reaction.organism && reaction.organism.length > 0)) && (
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
              <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                Enzyme Information
              </h3>
              <dl className="mt-3 space-y-2 text-sm">
                {reaction.ec_number && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">EC Number</dt>
                    <dd>
                      <a href={`https://enzyme.expasy.org/EC/${reaction.ec_number}`} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300">{reaction.ec_number}</a>
                    </dd>
                  </div>
                )}
                {reaction.enzyme_name && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Enzyme</dt>
                    <dd className="text-zinc-200">{reaction.enzyme_name}</dd>
                  </div>
                )}
                {reaction.rhea_id && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">RHEA</dt>
                    <dd>
                      <a href={`https://www.rhea-db.org/rhea/${reaction.rhea_id.replace("RHEA:", "")}`} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300">{reaction.rhea_id}</a>
                    </dd>
                  </div>
                )}
                {reaction.km_mm != null && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Km</dt>
                    <dd className="text-zinc-200">{reaction.km_mm} mM</dd>
                  </div>
                )}
                {reaction.kcat_sec != null && (
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">kcat</dt>
                    <dd className="text-zinc-200">{reaction.kcat_sec} s&#x207b;&#xb9;</dd>
                  </div>
                )}
              </dl>
            </div>
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
              <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                Literature & Organisms
              </h3>
              {reaction.pmid && reaction.pmid.length > 0 ? (
                <div className="mt-3 space-y-1">
                  <p className="text-xs text-zinc-500">References</p>
                  <div className="flex flex-wrap gap-2">
                    {reaction.pmid.map((pmid) => (
                      <a key={pmid} href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}`} target="_blank" rel="noopener noreferrer" className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs text-blue-400 hover:text-blue-300">
                        PMID:{pmid}
                      </a>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="mt-3 text-sm text-zinc-500">No literature references</p>
              )}
              {reaction.organism && reaction.organism.length > 0 && (
                <div className="mt-3 space-y-1">
                  <p className="text-xs text-zinc-500">Organisms</p>
                  <div className="flex flex-wrap gap-2">
                    {reaction.organism.map((org, i) => (
                      <span key={i} className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs italic text-zinc-300">{org}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
