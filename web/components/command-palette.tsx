"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
} from "@/components/ui/command";
import { searchCompounds } from "@/lib/search";
import { compounds } from "@/lib/data";
import { COMPOUND_TYPE_COLORS } from "@/lib/utils";
import {
  Home,
  Route,
  FlaskConical,
  Beaker,
  Network,
  Info,
} from "lucide-react";

const PAGES = [
  { label: "Dashboard", href: "/", icon: Home },
  { label: "Pathways", href: "/pathways", icon: Route },
  { label: "Compounds", href: "/compounds", icon: FlaskConical },
  { label: "Reactions", href: "/reactions", icon: Beaker },
  { label: "Network", href: "/network", icon: Network },
  { label: "About", href: "/about", icon: Info },
];

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  // Keyboard shortcut
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  const results = query.length >= 1 ? searchCompounds(query, compounds, 8) : [];

  const handleSelect = useCallback(
    (href: string) => {
      setOpen(false);
      setQuery("");
      router.push(href);
    },
    [router]
  );

  return (
    <CommandDialog
      open={open}
      onOpenChange={setOpen}
      title="Command Palette"
      description="Search compounds and navigate pages"
    >
      <CommandInput
        placeholder="Search compounds or pages..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        {results.length > 0 && (
          <CommandGroup heading="Compounds">
            {results.map((compound) => (
              <CommandItem
                key={compound.id}
                value={`compound-${compound.id}-${compound.name}`}
                onSelect={() => handleSelect(`/compound/${compound.id}`)}
              >
                <div className="flex flex-1 items-center gap-3">
                  <div className="flex-1">
                    <span className="text-sm text-zinc-100">
                      {compound.name}
                    </span>
                  </div>
                  <span
                    className={`text-xs capitalize ${COMPOUND_TYPE_COLORS[compound.type]}`}
                  >
                    {compound.type.replace("_", " ")}
                  </span>
                  {compound.chirality !== "achiral" && (
                    <span className="text-xs text-zinc-500">
                      {compound.chirality}
                    </span>
                  )}
                </div>
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {results.length > 0 && <CommandSeparator />}

        <CommandGroup heading="Pages">
          {PAGES.map((page) => (
            <CommandItem
              key={page.href}
              value={`page-${page.label}`}
              onSelect={() => handleSelect(page.href)}
            >
              <page.icon className="h-4 w-4 text-zinc-400" />
              <span>{page.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
