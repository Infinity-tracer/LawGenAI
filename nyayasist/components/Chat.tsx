

import React, { useState, useRef } from 'react';
import { LawIcon, PlusIcon, FolderIcon, SendIcon, PaperclipIcon } from './Icons';
import { Message, ChatMode, CaseResult, LawComparison } from '../types';
import { uploadPDF, chatWithPDF, searchKanoon, compareLawSection } from '../utils/apiService';
import LawComparisonCard from './LawComparisonCard';

interface ChatProps {
  onLogout: () => void;
}

const Chat: React.FC<ChatProps> = ({ onLogout }) => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatMode, setChatMode] = useState<ChatMode>(ChatMode.PDF_CHAT);
  const [pdfUploaded, setPdfUploaded] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const history = [
    { id: '1', title: 'IPC Section 302 Interpretation', group: 'Active Cases' },
    { id: '2', title: 'Property Dispute - Haryana', group: 'Active Cases' },
    { id: '3', title: 'Contract Law Precedents', group: 'Research' },
    { id: '4', title: 'Labor Act Summary', group: 'Research' },
  ];

  const generateId = () => Math.random().toString(36).substring(2, 15);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: input,
      timestamp: new Date(),
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      if (chatMode === ChatMode.PDF_CHAT) {
        if (!pdfUploaded) {
          const errorMessage: Message = {
            id: generateId(),
            role: 'assistant',
            content: '⚠️ Please upload a PDF document first before asking questions.',
            timestamp: new Date(),
            type: 'text'
          };
          setMessages(prev => [...prev, errorMessage]);
        } else {
          const response = await chatWithPDF(input);
          const assistantMessage: Message = {
            id: generateId(),
            role: 'assistant',
            content: response.answer,
            timestamp: new Date(),
            type: 'text',
            law_comparisons: response.law_comparisons
          };
          setMessages(prev => [...prev, assistantMessage]);
        }
      } else if (chatMode === ChatMode.LAW_COMPARISON) {
        // Law Comparison Mode - Support single or multiple sections
        const cleanInput = input.trim();

        // Parse input to extract law type and sections
        let lawType = 'IPC'; // Default
        let sectionNumbers: string[] = [];

        // Detect law type from input
        if (/(?:^|\s)(CRPC|CrPC)(?:\s|$)/i.test(cleanInput)) {
          lawType = 'CRPC';
        } else if (/(?:^|\s)IEA(?:\s|$)/i.test(cleanInput)) {
          lawType = 'IEA';
        } else if (/(?:^|\s)IPC(?:\s|$)/i.test(cleanInput)) {
          lawType = 'IPC';
        }

        // Extract all section numbers (digits optionally followed by letters)
        // Match patterns like: 302, 304A, 120-B, 120B, etc.
        const sectionMatches = cleanInput.matchAll(/\b(\d+[A-Z]?(-[A-Z])?)\b/gi);
        for (const match of sectionMatches) {
          const section = match[1].toUpperCase().replace('-', '');
          if (!sectionNumbers.includes(section)) {
            sectionNumbers.push(section);
          }
        }

        // If no sections found, show error
        if (sectionNumbers.length === 0) {
          const errorMessage: Message = {
            id: generateId(),
            role: 'assistant',
            content: '⚠️ No valid section numbers found. Please enter section numbers (e.g., "IPC 302 376" or "CRPC 154 156").',
            timestamp: new Date(),
            type: 'text'
          };
          setMessages(prev => [...prev, errorMessage]);
          return;
        }

        try {
          // Get comparisons for all sections
          const comparisons: LawComparison[] = [];
          const notFound: string[] = [];

          for (const section of sectionNumbers) {
            try {
              const response = await compareLawSection(lawType, section);
              if (response.success && response.comparison) {
                comparisons.push(response.comparison);
              } else {
                notFound.push(section);
              }
            } catch (err) {
              notFound.push(section);
            }
          }

          // Display results
          if (comparisons.length > 0) {
            const assistantMessage: Message = {
              id: generateId(),
              role: 'assistant',
              content: comparisons.length === 1
                ? `Comparison for ${lawType} Section ${sectionNumbers[0]}:`
                : `Found ${comparisons.length} comparison${comparisons.length > 1 ? 's' : ''} for ${lawType} sections:`,
              timestamp: new Date(),
              type: 'comparisons',
              law_comparisons: comparisons
            };
            setMessages(prev => [...prev, assistantMessage]);

            // If some sections were not found, add a note
            if (notFound.length > 0) {
              const warningMessage: Message = {
                id: generateId(),
                role: 'assistant',
                content: `⚠️ Note: No comparison data found for ${lawType} section${notFound.length > 1 ? 's' : ''}: ${notFound.join(', ')}`,
                timestamp: new Date(),
                type: 'text'
              };
              setMessages(prev => [...prev, warningMessage]);
            }
          } else {
            const errorMessage: Message = {
              id: generateId(),
              role: 'assistant',
              content: `❌ No comparison data found for ${lawType} section${sectionNumbers.length > 1 ? 's' : ''}: ${sectionNumbers.join(', ')}. Please check the section numbers.`,
              timestamp: new Date(),
              type: 'text'
            };
            setMessages(prev => [...prev, errorMessage]);
          }
        } catch (error: any) {
          const errorMessage: Message = {
            id: generateId(),
            role: 'assistant',
            content: `⚠️ Error: ${error.message}`,
            timestamp: new Date(),
            type: 'text'
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      } else {
        // Kanoon Search
        const response = await searchKanoon(input);
        const assistantMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: response.cases.length > 0
            ? `Found ${response.total_found} relevant cases. Showing top ${response.cases.length}:`
            : '❌ No relevant cases found for your query.',
          timestamp: new Date(),
          type: 'cases',
          cases: response.cases,
          law_comparisons: response.law_comparisons
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error: any) {
      const errorMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: `⚠️ Error: ${error.message}`,
        timestamp: new Date(),
        type: 'text'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const pdfFiles = (Array.from(files) as File[]).filter(f => f.type === 'application/pdf');
    if (pdfFiles.length === 0) {
      setUploadStatus('⚠️ Please select valid PDF documents.');
      return;
    }

    setUploadStatus('📄 Uploading and processing...');
    setIsLoading(true);

    try {
      const response = await uploadPDF(pdfFiles);
      setPdfUploaded(true);
      setUploadStatus(`✅ ${response.message} (${response.chunks_processed} chunks created)`);

      const systemMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: `📄 **PDF Uploaded Successfully**\n\nProcessed ${pdfFiles.length} document(s) into ${response.chunks_processed} chunks. You can now ask questions about the content.`,
        timestamp: new Date(),
        type: 'text'
      };
      setMessages(prev => [...prev, systemMessage]);
    } catch (error: any) {
      setUploadStatus(`⚠️ Upload failed: ${error.message}`);
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleNewChat = () => {
    setMessages([]);
    setUploadStatus('');
  };

  const renderMessage = (msg: Message) => {
    if (msg.type === 'cases' && msg.cases && msg.cases.length > 0) {
      return (
        <div className="space-y-4">
          <p className="text-[#f5f5f5]/80">{msg.content}</p>
          {msg.cases.map((caseItem, idx) => (
            <div key={caseItem.doc_id} className="border border-[#3d2b1f] bg-[#1a1c1b] p-4">
              <a
                href={caseItem.case_link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#d4af37] hover:underline font-medium"
              >
                {idx + 1}. {caseItem.title}
              </a>
              <p className="text-[#f5f5f5]/60 mt-2 text-sm leading-relaxed border-l-2 border-[#d4af37]/30 pl-3">
                {caseItem.snippet}
              </p>
            </div>
          ))}
        </div>
      );
    }

    // Render law comparisons if present
    const hasComparisons = msg.law_comparisons && msg.law_comparisons.length > 0;

    return (
      <div className="space-y-4">
        <p className="whitespace-pre-wrap">{msg.content}</p>
        {hasComparisons && (
          <div className="space-y-4 mt-4">
            <div className="text-[#d4af37] text-xs uppercase tracking-wide font-bold border-t border-[#3d2b1f] pt-4">
              ⚖️ Law Comparisons Detected
            </div>
            {msg.law_comparisons!.map((comp, idx) => (
              <LawComparisonCard key={idx} comparison={comp} />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-[#0b0d0c] text-[#f5f5f5]">
      {/* Sidebar */}
      <aside className="w-80 bg-[#161817] flex flex-col border-r border-[#3d2b1f]">
        <div className="p-6">
          <div className="flex items-center mb-8">
            <div className="border-2 border-[#d4af37] p-0.5 mr-3">
              <img
                src="/college-logo.png"
                alt="College Logo"
                className="h-12 w-12 object-contain"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                }}
              />
            </div>
            <h2 className="text-xl font-bold tracking-tight serif text-[#f5f5f5]">NYAYASIST</h2>
          </div>

          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 bg-[#3d2b1f] border border-[#d4af37]/30 p-3 text-sm hover:bg-[#4d3b2f] transition-colors mb-6 font-medium"
          >
            <PlusIcon />
            <span>New Case Research</span>
          </button>

          {/* Mode Toggle */}
          <div className="mb-6">
            <div className="text-[#d4af37] text-[10px] uppercase tracking-[0.3em] font-bold mb-3 opacity-70">
              Research Mode
            </div>
            <div className="space-y-2">
              <button
                onClick={() => setChatMode(ChatMode.PDF_CHAT)}
                className={`w-full text-left p-3 text-sm border-l-2 transition-all ${chatMode === ChatMode.PDF_CHAT
                  ? 'bg-[#3d2b1f] border-[#d4af37] text-[#f5f5f5]'
                  : 'border-transparent text-[#f5f5f5]/60 hover:bg-[#3d2b1f]/50'
                  }`}
              >
                📄 Chat with PDF
              </button>
              <button
                onClick={() => setChatMode(ChatMode.KANOON_SEARCH)}
                className={`w-full text-left p-3 text-sm border-l-2 transition-all ${chatMode === ChatMode.KANOON_SEARCH
                  ? 'bg-[#3d2b1f] border-[#d4af37] text-[#f5f5f5]'
                  : 'border-transparent text-[#f5f5f5]/60 hover:bg-[#3d2b1f]/50'
                  }`}
              >
                ⚖️ Indian Kanoon Search
              </button>
              <button
                onClick={() => setChatMode(ChatMode.LAW_COMPARISON)}
                className={`w-full text-left p-3 text-sm border-l-2 transition-all ${chatMode === ChatMode.LAW_COMPARISON
                  ? 'bg-[#3d2b1f] border-[#d4af37] text-[#f5f5f5]'
                  : 'border-transparent text-[#f5f5f5]/60 hover:bg-[#3d2b1f]/50'
                  }`}
              >
                📊 Law Comparison
              </button>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-4 space-y-6">
          <div>
            <div className="flex items-center gap-2 text-[#d4af37] text-[10px] uppercase tracking-[0.3em] font-bold mb-4 px-2 opacity-70">
              <FolderIcon />
              <span>Active Cases</span>
            </div>
            {history.filter(h => h.group === 'Active Cases').map(item => (
              <button key={item.id} className="w-full text-left p-3 text-sm hover:bg-[#3d2b1f] border-l-2 border-transparent hover:border-[#d4af37] truncate opacity-80 hover:opacity-100 font-light transition-all">
                {item.title}
              </button>
            ))}
          </div>

          <div>
            <div className="flex items-center gap-2 text-[#d4af37] text-[10px] uppercase tracking-[0.3em] font-bold mb-4 px-2 opacity-70">
              <FolderIcon />
              <span>Research Folders</span>
            </div>
            {history.filter(h => h.group === 'Research').map(item => (
              <button key={item.id} className="w-full text-left p-3 text-sm hover:bg-[#3d2b1f] border-l-2 border-transparent hover:border-[#d4af37] truncate opacity-80 hover:opacity-100 font-light transition-all">
                {item.title}
              </button>
            ))}
          </div>
        </nav>

        <div className="p-4 border-t border-[#3d2b1f] bg-[#0b0d0c]">
          <button
            onClick={onLogout}
            className="w-full text-left p-3 text-sm text-red-400 hover:bg-red-900/10 font-light transition-colors"
          >
            Leave Chambers (Logout)
          </button>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-[#3d2b1f] bg-[#0b0d0c] text-center">
          <p className="text-[#d4af37] text-[10px] tracking-wide">
            © {new Date().getFullYear()} All Rights Reserved
          </p>
          <p className="text-[#f5f5f5]/50 text-[9px] mt-1 tracking-widest uppercase">
            Developed by <span className="text-[#d4af37]">NAYASRI P</span> & <span className="text-[#d4af37]">NITYA SHARMA</span>
          </p>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        <header className="h-16 border-b border-[#3d2b1f] flex items-center px-8 justify-between bg-[#0b0d0c]/80 backdrop-blur-md z-10">
          <div className="flex items-center gap-3">
            <div className="border-2 border-[#d4af37] p-0.5">
              <img
                src="/college-logo.png"
                alt="College Logo"
                className="h-10 w-10 object-contain"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                }}
              />
            </div>
            <div className="text-sm font-medium text-[#d4af37] serif tracking-[0.1em]">
              {chatMode === ChatMode.PDF_CHAT ? '📄 PDF Analysis Mode' :
                chatMode === ChatMode.KANOON_SEARCH ? '⚖️ Indian Kanoon Search' :
                  '📊 Law Comparison Mode'}
            </div>
          </div>
          <div className="flex gap-4 text-xs">
            {chatMode === ChatMode.PDF_CHAT && (
              <span className={pdfUploaded ? 'text-green-400' : 'text-[#f5f5f5]/40'}>
                {pdfUploaded ? '✓ PDF Loaded' : 'No PDF uploaded'}
              </span>
            )}
            <span className="text-[#f5f5f5]/40 italic">API: Connected</span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center">
              <div className="max-w-2xl text-center space-y-8">
                <div className="flex justify-center text-[#d4af37]">
                  <LawIcon className="w-24 h-24 opacity-20" />
                </div>
                <h1 className="text-4xl serif font-bold text-[#f5f5f5] tracking-tight">
                  {chatMode === ChatMode.PDF_CHAT
                    ? 'Upload a PDF to begin analysis'
                    : chatMode === ChatMode.KANOON_SEARCH
                      ? 'Search Indian legal precedents'
                      : 'Compare Old vs New Criminal Laws'}
                </h1>
                <p className="text-[#f5f5f5]/60 leading-relaxed font-light text-lg">
                  {chatMode === ChatMode.PDF_CHAT
                    ? 'Upload legal documents, contracts, or case files and ask questions about their content.'
                    : chatMode === ChatMode.KANOON_SEARCH
                      ? 'Search for relevant case law, interpret sections of law, or find precedents from Indian courts.'
                      : 'Compare old Indian criminal codes (IPC, CrPC, IEA) with new codes (BNS, BNSS, BEA). Enter a section like "IPC 302" or "CRPC 154".'}
                </p>

                {uploadStatus && (
                  <div className="p-4 border border-[#3d2b1f] bg-[#1a1c1b] text-sm">
                    {uploadStatus}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4 mt-12">
                  {chatMode === ChatMode.PDF_CHAT ? (
                    <>
                      <button
                        onClick={triggerFileUpload}
                        className="p-5 border border-[#3d2b1f] bg-[#1a1c1b] text-sm text-left hover:border-[#d4af37] opacity-80 transition-all group"
                      >
                        <div className="text-[#d4af37] mb-2 font-bold tracking-widest text-[10px] uppercase opacity-70 group-hover:opacity-100">Upload Document</div>
                        <span className="font-light">"Click to upload PDF files for analysis"</span>
                      </button>
                      <button className="p-5 border border-[#3d2b1f] bg-[#1a1c1b] text-sm text-left hover:border-[#d4af37] opacity-80 transition-all group">
                        <div className="text-[#d4af37] mb-2 font-bold tracking-widest text-[10px] uppercase opacity-70 group-hover:opacity-100">Ask Questions</div>
                        <span className="font-light">"What are the key terms of this contract?"</span>
                      </button>
                    </>
                  ) : chatMode === ChatMode.KANOON_SEARCH ? (
                    <>
                      <button className="p-5 border border-[#3d2b1f] bg-[#1a1c1b] text-sm text-left hover:border-[#d4af37] opacity-80 transition-all group">
                        <div className="text-[#d4af37] mb-2 font-bold tracking-widest text-[10px] uppercase opacity-70 group-hover:opacity-100">Criminal Law</div>
                        <span className="font-light">"IPC Section 302 murder cases"</span>
                      </button>
                      <button className="p-5 border border-[#3d2b1f] bg-[#1a1c1b] text-sm text-left hover:border-[#d4af37] opacity-80 transition-all group">
                        <div className="text-[#d4af37] mb-2 font-bold tracking-widest text-[10px] uppercase opacity-70 group-hover:opacity-100">Constitutional Law</div>
                        <span className="font-light">"Article 21 right to privacy judgments"</span>
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => setInput('IPC 302')}
                        className="p-5 border border-[#3d2b1f] bg-[#1a1c1b] text-sm text-left hover:border-[#d4af37] opacity-80 transition-all group">
                        <div className="text-[#d4af37] mb-2 font-bold tracking-widest text-[10px] uppercase opacity-70 group-hover:opacity-100">Murder</div>
                        <span className="font-light">"IPC 302 → BNS 103"</span>
                      </button>
                      <button
                        onClick={() => setInput('IPC 376')}
                        className="p-5 border border-[#3d2b1f] bg-[#1a1c1b] text-sm text-left hover:border-[#d4af37] opacity-80 transition-all group">
                        <div className="text-[#d4af37] mb-2 font-bold tracking-widest text-[10px] uppercase opacity-70 group-hover:opacity-100">Rape</div>
                        <span className="font-light">"IPC 376 → BNS 64-70"</span>
                      </button>
                      <button
                        onClick={() => setInput('CRPC 154')}
                        className="p-5 border border-[#3d2b1f] bg-[#1a1c1b] text-sm text-left hover:border-[#d4af37] opacity-80 transition-all group">
                        <div className="text-[#d4af37] mb-2 font-bold tracking-widest text-[10px] uppercase opacity-70 group-hover:opacity-100">FIR</div>
                        <span className="font-light">"CrPC 154 → BNSS 173"</span>
                      </button>
                      <button
                        onClick={() => setInput('IEA 45')}
                        className="p-5 border border-[#3d2b1f] bg-[#1a1c1b] text-sm text-left hover:border-[#d4af37] opacity-80 transition-all group">
                        <div className="text-[#d4af37] mb-2 font-bold tracking-widest text-[10px] uppercase opacity-70 group-hover:opacity-100">Expert Opinion</div>
                        <span className="font-light">"IEA 45 → BEA 39"</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-4 ${msg.role === 'user'
                      ? 'bg-[#3d2b1f] border border-[#d4af37]/30'
                      : 'bg-[#1a1c1b] border border-[#3d2b1f]'
                      }`}
                  >
                    <div className="text-[10px] uppercase tracking-[0.2em] text-[#d4af37] mb-2 opacity-70">
                      {msg.role === 'user' ? 'You' : 'NyayAssist'}
                    </div>
                    {renderMessage(msg)}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-[#1a1c1b] border border-[#3d2b1f] p-4">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-[#d4af37] mb-2 opacity-70">
                      NyayAssist
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-[#d4af37] rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-[#d4af37] rounded-full animate-pulse delay-100"></div>
                      <div className="w-2 h-2 bg-[#d4af37] rounded-full animate-pulse delay-200"></div>
                      <span className="text-[#f5f5f5]/40 text-sm ml-2">
                        {chatMode === ChatMode.PDF_CHAT ? 'Analyzing document...' : 'Searching Indian Kanoon...'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Chat Input with PDF Upload */}
        <div className="p-8 bg-gradient-to-t from-[#0b0d0c] via-[#0b0d0c] to-transparent">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto relative group">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf"
              multiple
              className="hidden"
            />
            {chatMode === ChatMode.PDF_CHAT && (
              <button
                type="button"
                onClick={triggerFileUpload}
                disabled={isLoading}
                className="absolute left-5 top-1/2 -translate-y-1/2 text-[#d4af37] hover:text-[#f5f5f5] p-2 transition-colors disabled:opacity-50"
                title="Upload PDF for analysis"
              >
                <PaperclipIcon className="w-5 h-5" />
              </button>
            )}

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              placeholder={
                chatMode === ChatMode.PDF_CHAT
                  ? "Ask a question about your uploaded PDF..."
                  : chatMode === ChatMode.KANOON_SEARCH
                    ? "Search for cases, statutes, or legal precedents..."
                    : "Enter law section (e.g., IPC 302, CRPC 154, IEA 45)..."
              }
              className={`w-full bg-[#1a1c1b] border border-[#3d2b1f] text-[#f5f5f5] p-5 ${chatMode === ChatMode.PDF_CHAT ? 'pl-16' : 'pl-5'
                } pr-16 outline-none focus:border-[#d4af37] shadow-2xl font-light placeholder:text-[#f5f5f5]/20 transition-all disabled:opacity-50`}
            />

            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="absolute right-5 top-1/2 -translate-y-1/2 text-[#d4af37] hover:text-[#f5f5f5] p-2 transition-colors disabled:opacity-50"
            >
              <SendIcon />
            </button>
          </form>
          <div className="text-center mt-6 text-[10px] text-[#f5f5f5]/20 tracking-[0.5em] uppercase">
            Privileged and Confidential • AI Jurisprudence Protocol
          </div>
        </div>
      </main>
    </div>
  );
};

export default Chat;

