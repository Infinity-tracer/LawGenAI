
import React from 'react';
import { LawComparison } from '../types';

interface LawComparisonCardProps {
    comparison: LawComparison;
}

const LawComparisonCard: React.FC<LawComparisonCardProps> = ({ comparison }) => {
    const isOmitted = comparison.new_section === 'OMITTED';

    return (
        <div className="border border-[#3d2b1f] bg-[#1a1c1b] overflow-hidden">
            {/* Header */}
            <div className="bg-[#3d2b1f]/30 px-4 py-3 border-b border-[#3d2b1f]">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="text-[#d4af37] text-xs uppercase tracking-widest font-bold">
                            Law Comparison
                        </div>
                        <div className="text-[#f5f5f5]/40 text-xs">
                            Effective: July 1, 2024
                        </div>
                    </div>
                    {isOmitted && (
                        <div className="bg-red-900/30 border border-red-500/30 px-3 py-1 text-xs text-red-400 uppercase tracking-wide font-bold">
                            Section Omitted
                        </div>
                    )}
                </div>
            </div>

            {/* Comparison Content */}
            <div className="p-6">
                {isOmitted ? (
                    // Omitted Section Layout
                    <div className="space-y-4">
                        <div className="border-l-4 border-red-500/50 pl-4">
                            <div className="text-[#d4af37] text-sm uppercase tracking-wide mb-2 font-semibold">
                                {comparison.old_law} Section {comparison.old_section}
                            </div>
                            <div className="text-[#f5f5f5] font-medium mb-2">
                                {comparison.old_title}
                            </div>
                            <div className="text-red-400 text-sm italic">
                                ⚠️ This section has been omitted in the new {comparison.new_law}
                            </div>
                        </div>

                        <div className="bg-[#3d2b1f]/20 p-4 border border-[#3d2b1f]">
                            <div className="text-[#f5f5f5]/60 text-sm mb-2 font-semibold">Changes:</div>
                            <div className="text-[#f5f5f5]/80 text-sm leading-relaxed">
                                {comparison.changes}
                            </div>
                        </div>
                    </div>
                ) : (
                    // Side-by-Side Comparison Layout
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Old Law (Left Side) */}
                        <div className="space-y-3">
                            <div className="border-l-4 border-red-500/40 pl-4">
                                <div className="text-red-300 text-xs uppercase tracking-wide mb-1 opacity-70">
                                    Old Law (Replaced)
                                </div>
                                <div className="text-[#d4af37] text-lg font-semibold mb-1">
                                    {comparison.old_law} § {comparison.old_section}
                                </div>
                                <div className="text-[#f5f5f5] text-sm font-medium">
                                    {comparison.old_title}
                                </div>
                            </div>
                        </div>

                        {/* Arrow Indicator */}
                        <div className="hidden md:flex absolute left-1/2 -ml-6 mt-4 items-center justify-center">
                            <div className="bg-[#d4af37] text-[#0b0d0c] rounded-full w-12 h-12 flex items-center justify-center text-xl font-bold shadow-lg border-2 border-[#3d2b1f]">
                                →
                            </div>
                        </div>

                        {/* New Law (Right Side) */}
                        <div className="space-y-3">
                            <div className="border-l-4 border-green-500/40 pl-4">
                                <div className="text-green-300 text-xs uppercase tracking-wide mb-1 opacity-70">
                                    New Law (Current)
                                </div>
                                <div className="text-[#d4af37] text-lg font-semibold mb-1">
                                    {comparison.new_law} § {comparison.new_section}
                                </div>
                                <div className="text-[#f5f5f5] text-sm font-medium">
                                    {comparison.new_title}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Changes Section (Always Shown for Non-Omitted) */}
                {!isOmitted && (
                    <div className="mt-6 pt-6 border-t border-[#3d2b1f]">
                        <div className="flex items-start gap-3">
                            <div className="text-[#d4af37] text-xs uppercase tracking-widest font-bold mt-1">
                                📝 Key Changes:
                            </div>
                            <div className="flex-1 text-[#f5f5f5]/80 text-sm leading-relaxed">
                                {comparison.changes}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default LawComparisonCard;
