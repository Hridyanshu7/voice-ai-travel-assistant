import React, { useState } from 'react';
import { Sun, Moon, Coffee, MapPin, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ItineraryBlock {
    time_block: string;
    poi: {
        name: string;
        description: string;
        category: string;
        average_duration_minutes: number;
        rating?: number;
        details?: Record<string, any>;
    };
    start_time?: string;
    end_time?: string;
    travel_time_from_previous?: string;
}

interface DayItinerary {
    day_number: number;
    blocks: ItineraryBlock[];
}

interface Itinerary {
    trip_title: string;
    days: DayItinerary[];
    total_cost_estimate?: string;
}

interface ItineraryViewProps {
    itinerary: Itinerary;
}

export function ItineraryView({ itinerary }: ItineraryViewProps) {
    const [activeDay, setActiveDay] = useState(1);

    const currentDay = itinerary.days.find(d => d.day_number === activeDay);

    const getIconForBlock = (block: string) => {
        switch (block) {
            case "Morning": return <Coffee className="w-5 h-5 text-orange-500" />;
            case "Afternoon": return <Sun className="w-5 h-5 text-yellow-500" />;
            case "Evening": return <Moon className="w-5 h-5 text-indigo-500" />;
            default: return <Clock className="w-5 h-5 text-slate-400" />;
        }
    };

    return (
        <div className="w-full max-w-2xl bg-white rounded-xl shadow-sm border overflow-hidden">
            <div className="p-6 border-b bg-slate-50">
                <h2 className="text-2xl font-bold text-slate-900">{itinerary.trip_title}</h2>
                {itinerary.total_cost_estimate && (
                    <span className="text-sm text-slate-500 mt-1 block">Est. Budget: {itinerary.total_cost_estimate}</span>
                )}
            </div>

            {/* Day Tabs */}
            <div className="flex border-b overflow-x-auto">
                {itinerary.days.map((day) => (
                    <button
                        key={day.day_number}
                        onClick={() => setActiveDay(day.day_number)}
                        className={cn(
                            "flex-1 py-3 px-4 text-sm font-medium whitespace-nowrap transition-colors border-b-2",
                            activeDay === day.day_number
                                ? "border-blue-600 text-blue-600 bg-blue-50/50"
                                : "border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                        )}
                    >
                        Day {day.day_number}
                    </button>
                ))}
            </div>

            {/* Timeline */}
            <div className="p-6">
                <div className="space-y-8">
                    {currentDay?.blocks.map((block, idx) => (
                        <div key={idx} className="relative pl-8 border-l-2 border-slate-100 last:border-0 pb-8 last:pb-0">
                            {/* Icon / Bullet */}
                            <div className="absolute -left-[11px] top-0 bg-white p-1 border rounded-full shadow-sm">
                                {getIconForBlock(block.time_block)}
                            </div>

                            <div className="flex flex-col gap-1">
                                <div className="flex items-baseline justify-between">
                                    <h4 className="font-semibold text-slate-900">{block.time_block}</h4>
                                    <span className="text-xs font-mono text-slate-400">{block.start_time} - {block.end_time}</span>
                                </div>

                                {block.travel_time_from_previous && (
                                    <div className="top-0 text-xs text-slate-400 italic mb-2 flex items-center gap-1">
                                        <span className="w-1 h-1 rounded-full bg-slate-300"></span>
                                        Travel: {block.travel_time_from_previous}
                                    </div>
                                )}

                                <div className="p-4 bg-slate-50 rounded-lg border hover:shadow-md transition-shadow">
                                    <div className="flex justify-between items-start">
                                        <h3 className="font-medium text-slate-800 text-lg">{block.poi?.name || "Relax"}</h3>
                                        <span className="text-xs px-2 py-1 bg-white rounded border text-slate-500">{block.poi?.category}</span>
                                    </div>
                                    <p className="text-sm text-slate-600 mt-2 leading-relaxed">
                                        {block.poi?.description}
                                    </p>
                                    <div className="mt-3 flex gap-4 text-xs text-slate-500">
                                        <span className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" /> {block.poi?.average_duration_minutes} mins
                                        </span>
                                        <span className="flex items-center gap-1">
                                            ★ {block.poi?.rating || "N/A"}
                                        </span>
                                    </div>

                                    {/* Additional Details (Costs, Timings, Tips) */}
                                    {block.poi?.details && Object.keys(block.poi.details).length > 0 && (
                                        <div className="mt-3 pt-3 border-t grid grid-cols-2 gap-2 text-xs">
                                            {Object.entries(block.poi.details).map(([key, value]) => (
                                                <div key={key} className="flex flex-col">
                                                    <span className="font-semibold text-slate-700 capitalize">{key.replace(/_/g, " ")}:</span>
                                                    <span className="text-slate-600">{String(value)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
