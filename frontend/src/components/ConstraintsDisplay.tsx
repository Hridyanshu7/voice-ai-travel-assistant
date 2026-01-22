import React from 'react';
import { Check, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TripConstraints {
    destination_city?: string;
    start_date?: string;
    end_date?: string;
    duration_days?: number;
    budget_level?: string;
    travelers_count?: number;
    pace?: string;
    interests?: string[];
    missing_info?: string[];
    clarification_question?: string;
}

interface ConstraintsDisplayProps {
    constraints: TripConstraints;
    onConfirm: () => void;
    onEdit: () => void;
}

export function ConstraintsDisplay({ constraints, onConfirm, onEdit }: ConstraintsDisplayProps) {
    const isComplete = !constraints.missing_info || constraints.missing_info.length === 0;

    return (
        <div className="w-full max-w-md bg-white rounded-lg border shadow-sm p-6 space-y-4">
            <h3 className="text-lg font-semibold text-slate-900 border-b pb-2">Trip Plan Details</h3>

            <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <span className="text-slate-500 block">Destination</span>
                    <span className="font-medium text-slate-800">{constraints.destination_city || "—"}</span>
                </div>
                <div>
                    <span className="text-slate-500 block">Dates</span>
                    <span className="font-medium text-slate-800">
                        {constraints.start_date || constraints.duration_days ?
                            `${constraints.start_date || 'TBD'} (${constraints.duration_days || '?'} days)` : "—"}
                    </span>
                </div>
                <div>
                    <span className="text-slate-500 block">Key Interests</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                        {constraints.interests && constraints.interests.length > 0 ? (
                            constraints.interests.map((interest, i) => (
                                <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs border border-blue-100">
                                    {interest}
                                </span>
                            ))
                        ) : (
                            <span className="text-slate-400">—</span>
                        )}
                    </div>
                </div>
                <div>
                    <span className="text-slate-500 block">Pace & Budget</span>
                    <span className="font-medium text-slate-800">
                        {constraints.pace || "Moderate"}, {constraints.budget_level || "Standard"}
                    </span>
                </div>
            </div>

            {constraints.missing_info && constraints.missing_info.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-md p-3 text-sm text-amber-800 flex gap-2 items-start">
                    <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <div>
                        <p className="font-semibold">Missing Information:</p>
                        <p>{constraints.clarification_question || `Please specify: ${constraints.missing_info.join(", ")}`}</p>
                    </div>
                </div>
            )}

            <div className="flex gap-3 pt-2">
                <button
                    onClick={onEdit}
                    className="flex-1 py-2 px-4 rounded-md border border-slate-300 text-slate-700 font-medium hover:bg-slate-50 transition-colors"
                >
                    Add More Info (Voice)
                </button>
                {isComplete && (
                    <button
                        onClick={onConfirm}
                        className="flex-1 py-2 px-4 rounded-md bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                    >
                        <Check className="w-4 h-4" />
                        Generate Plan
                    </button>
                )}
            </div>
        </div>
    );
}
