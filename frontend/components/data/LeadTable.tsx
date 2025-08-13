"use client";

import * as React from "react";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable
} from "@tanstack/react-table";
import clsx from "clsx";

type Lead = {
  id: string;
  name: string;
  trade: string;      // Roofing, HVAC, etc.
  county: string;
  status: "New" | "Qualified" | "Contacted" | "Won" | "Lost";
};

const columns: ColumnDef<Lead>[] = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "trade", header: "Trade" },
  { accessorKey: "county", header: "County" },
  { accessorKey: "status", header: "Status" }
];

export default function LeadTable({ data }: { data: Lead[] }) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel()
  });

  return (
    <div className="rounded-xl border bg-white shadow-soft overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500">
          {table.getHeaderGroups().map(hg => (
            <tr key={hg.id}>
              {hg.headers.map(h => (
                <th key={h.id} className="text-left px-4 py-3">
                  {flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr key={row.id} className="border-t">
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className="px-4 py-3">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}