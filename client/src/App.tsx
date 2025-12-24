import Document from "./Document";
import { useEffect, useState } from "react";
import axios from "axios";
import LoadingOverlay from "./internal/LoadingOverlay";
import { showToast } from "./utils/utils";


const BACKEND_URL = "http://localhost:8000";

function App() {
  const [currentDocumentContent, setCurrentDocumentContent] = useState<string>("");

  // Loading state
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Document states
  const [currentDocumentId, setCurrentDocumentId] = useState<number>(0);
  const [versions, setVersions] = useState<any[]>([]);
  const [currentVersionNumber, setCurrentVersionNumber] = useState<number | null>(null);

  // AI Suggestion states
  const [suggestions, setSuggestions] = useState<any[]>([]);

  // AI Rephrase states
  const [selectedText, setSelectedText] = useState<string>("");
  const [rewriteOverlay, setRewriteOverlay] = useState<{ original: string; rewritten: string } | null>(null);
  const [isRewriteLoading, setIsRewriteLoading] = useState<boolean>(false);

  // AI Analyse states
  const [analysisResult, setAnalysisResult] = useState<{ score: number; problems: string[] } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Collapsibles states
  const [isRewriteOpen, setIsRewriteOpen] = useState(true);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(true);
  const [isSuggestionsOpen, setIsSuggestionsOpen] = useState(true);


  // Load the first patent on mount
  useEffect(() => {
    loadPatent(1);

    const handleSelectionChange = () => {
      const selection = window.getSelection();
      const editor = document.getElementById("document-editor");

      if (
        selection &&
        selection.toString().trim().length > 5 &&
        editor &&
        selection.anchorNode &&
        editor.contains(selection.anchorNode)
      ) {
        setSelectedText(selection.toString());
      } else {
        setSelectedText("");
      }
    };
    document.addEventListener("selectionchange", handleSelectionChange);
    return () => {
      document.removeEventListener("selectionchange", handleSelectionChange);
    };
  }, []);

  // === Backend: Load a document and its versions ===
  const loadPatent = async (documentNumber: number) => {
    setIsLoading(true);
    console.log("Loading patent:", documentNumber);
    try {
      const response = await axios.get(
        `${BACKEND_URL}/document/${documentNumber}`
      );
      setCurrentDocumentId(response.data.document_id);
      setCurrentVersionNumber(response.data.version_number);
      setCurrentDocumentContent(response.data.content);

      // get all versions
      const versionsResponse = await axios.get(
        `${BACKEND_URL}/documents/${documentNumber}/versions`
      );
      setVersions(versionsResponse.data);

      clearSuggestions();
      showToast(`Loaded Patent ${response.data.document_id} - Version ${response.data.version_number}`);

    } catch (error) {
      console.error("Error loading document:", error);
    }
    setIsLoading(false);
  };

  // === Backend: Switch to a specific version of the current document ===
  const switchVersion = async (versionNumber: number) => {
    console.log("switching version to " + versionNumber)
    try {
      const response = await axios.patch(
        `${BACKEND_URL}/documents/${currentDocumentId}/switch/${versionNumber}`
      );
      setCurrentDocumentContent(response.data.content);
      setCurrentVersionNumber(response.data.version_number);
      clearSuggestions();
      showToast(`Switched to Patent ${response.data.document_id} - Version ${response.data.version_number}`);

    } catch (error) {
      console.error("Error switching version:", error);
    }
  };

  // === Backend: Create a new version of the current document ===
  const createNewVersion = async () => {
    try {
      const response = await axios.post(
        `${BACKEND_URL}/documents/${currentDocumentId}/versions`,
        { content: currentDocumentContent }
      );
      setVersions([...versions, response.data]);
      setCurrentVersionNumber(response.data.version_number);

      showToast(`New version created: Patent ${response.data.document_id} - Version ${response.data.version_number}`);

    } catch (error) {
      console.error("Error creating version:", error);
    }
  };

  // === Backend: Save edits to the current version ===
  const saveVersion = async () => {
    if (!currentVersionNumber) return;
    try {
      const response = await axios.patch(
        `${BACKEND_URL}/documents/${currentDocumentId}/versions/${currentVersionNumber}`,
        { content: currentDocumentContent }
      );

      showToast(`Saved: Patent ${response.data.document_id} - Version ${response.data.version_number}`);

    } catch (error) {
      console.error("Error saving version:", error);
    }
  };

  // === AI: Request a rewrite of highlighted text ===
  const sendRewriteRequest = async () => {

    let widerContext = currentDocumentContent

    console.log("Claim : " + selectedText + " Wider Context : " + widerContext);
    if (!selectedText) return;

    try {

      console.log("Requesting rewrite, Claim : " + selectedText + " + Wider context : " + widerContext);

      setIsRewriteLoading(true);

      const response = await axios.post(`${BACKEND_URL}/ai/rewrite`, {
        claim: selectedText,
        content_html: widerContext,
      });

      const replacementText = response.data.result.replacement
      const errorText = response.data.result.error

      if (errorText && errorText !== "") {
        console.log("Rewrite Error : " + errorText)
      } else {
        console.log("Rewrite response : " + replacementText);

        setRewriteOverlay({
          original: selectedText,
          rewritten: replacementText,
        });
      }
    } catch (error) {
      console.error("Error rewriting text:", error);
    } finally {
      setIsRewriteLoading(false);
    }
  };

  // === Utility: Replace highlighted text in editor with AI suggestion ===
  function replaceTextInEditor(original: string, rewritten: string) {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return;

    const range = selection.getRangeAt(0);
    range.deleteContents();
    range.insertNode(document.createTextNode(rewritten));

    // Move the cursor to the end of the inserted text
    selection.removeAllRanges();
    const newRange = document.createRange();
    newRange.setStartAfter(range.endContainer);
    selection.addRange(newRange);
  }

  // === AI: Request analysis of the whole document ===
  const requestAnalysis = async () => {
    if (!currentDocumentContent) return;

    if (currentDocumentContent.length < 250) {
      showToast(`Document content is not enough to analyze, please write more..`)
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/ai/analyze`, {
        content_html: currentDocumentContent,
      });

      setAnalysisResult(response.data.result);

      showToast("Patent analysis updated!");

    } catch (error) {
      console.error("Error analyzing document:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // === Utility: Clear AI analysis results ===
  const clearAnalysis = () => {
    setAnalysisResult(null);
    showToast("Patent analysis cleared!");
  };

  // === Utility: Clear AI suggestions ===
  const clearSuggestions = () => {
    setSuggestions([]);
  };


  // === RENDER UI ===
  return (
    (
      <div className="flex flex-col h-full w-full">
        {(isLoading || isRewriteLoading) && <LoadingOverlay />}

        {/* Header */}
        <header className="flex items-center justify-end px-6 bg-black text-white h-[80px] shadow-md">
          <div className="flex gap-4">
            <button
              onClick={() => loadPatent(1)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-white font-medium transition"
            >
              Patent 1
            </button>
            <button
              onClick={() => loadPatent(2)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-white font-medium transition"
            >
              Patent 2
            </button>
          </div>
        </header>

        {/* Main Content */}
        <div className="flex flex-1 gap-4 px-6 py-4 h-[calc(100%-80px)] min-h-0">

          {/* Editor Area */}
          <div className="flex-1 flex flex-col border rounded-lg shadow-md p-4 min-h-0">
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-2xl font-semibold text-[#213547] opacity-90">
                Patent {currentDocumentId}
              </h2>

              <div className="flex items-center gap-2">

                <button
                  onClick={saveVersion}
                  className="px-4 py-2 h-10 bg-blue-600 hover:bg-green-500 text-white rounded text-sm font-medium transition"
                >
                  Save
                </button>

                <button
                  onClick={createNewVersion}
                  className="px-4 py-2 h-10 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium transition"
                >
                  Save as
                </button>

                <p className="text-sm font-bold text-gray-500">Version:</p>

                <select
                  value={currentVersionNumber ?? ""}
                  onChange={(e) => switchVersion(Number(e.target.value))}
                  className="border rounded px-3 py-2 h-10 text-sm"
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.version_number}>
                      {v.version_number}
                    </option>
                  ))}
                </select>

              </div>
            </div>

            {/* Document Editor */}
            <div id="document-editor" className="flex-1 min-h-0 overflow-y-auto">
              <Document
                onContentChange={setCurrentDocumentContent}
                content={currentDocumentContent}
                onSuggestions={setSuggestions}
                onSelectionChange={setSelectedText}
              />
            </div>
          </div>


          {/* Sidebar: AI Features (Rephrase / Analysis / Suggestions) */}
          <div className="flex flex-col gap-4 w-80 h-full">

            {/* AI Rewrite Box */}
            <div className="border rounded-lg shadow-md p-4 bg-white">
              <div
                className="flex justify-between items-center mb-2 cursor-pointer"
                onClick={() => setIsRewriteOpen(!isRewriteOpen)}
              >
                <h3 className="font-bold text-lg">AI Rephrase</h3>
                <span>{isRewriteOpen ? "▾" : "▸"}</span>
              </div>

              {isRewriteOpen && (
                <>
                  {/* Selected text preview */}
                  <textarea
                    value={
                      selectedText.length > 80
                        ? `${selectedText.slice(0, 20)} ... ${selectedText.slice(-20)}`
                        : selectedText
                    }
                    readOnly
                    placeholder="Select text.."
                    className="border rounded p-2 w-full mb-2 text-sm bg-gray-100 text-gray-700"
                  />

                  <div className="flex justify-end">
                    <button
                      onClick={sendRewriteRequest}
                      disabled={!selectedText}
                      className="custom-btn"
                    >
                      Rephrase for Clarity
                    </button>
                  </div>
                </>
              )}
            </div>

            {/* AI Analysis Box */}
            <div className="border rounded-lg shadow-md p-4 bg-white">
              {/* Header with collapsible toggle */}
              <div
                className="flex justify-between items-center mb-2 cursor-pointer"
                onClick={() => setIsAnalysisOpen(!isAnalysisOpen)}
              >
                <h3 className="font-bold text-lg">AI Analysis</h3>
                <span className="text-base">{isAnalysisOpen ? "▾" : "▸"}</span>
              </div>

              {/* Collapsible content */}
              {isAnalysisOpen && (
                <>
                  {/* Show results if available */}
                  {analysisResult && (
                    <>
                      <div className="mb-4">
                        <p className="font-semibold mb-1">Quality Score</p>
                        <div className="w-full bg-gray-200 rounded-full h-4">
                          <div
                            className="h-4 rounded-full bg-green-500"
                            style={{ width: `${analysisResult.score}%` }}
                          ></div>
                        </div>
                        <p className="mt-1 text-sm text-gray-600">{analysisResult.score} / 100</p>
                      </div>

                      <div className="flex-1 overflow-y-auto border rounded p-2">
                        <h4 className="font-semibold mb-2">Problematic Areas</h4>
                        {analysisResult.problems.length === 0 ? (
                          <p className="text-gray-500 text-sm">No major problems detected 🎉</p>
                        ) : (
                          <ul className="list-disc pl-5 space-y-1 text-sm text-red-600">
                            {analysisResult.problems.map((p, i) => (
                              <li key={i}>{p}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </>
                  )}

                  {/* AI Analyze - Buttons */}
                  <div className="flex justify-end mb-0 py-0 gap-0">

                    {/* Analyse Button */}
                    <button
                      onClick={requestAnalysis}
                      className="custom-btn"
                      disabled={currentDocumentContent.length < 250 || isAnalyzing}
                    >
                      {isAnalyzing ? "Analysing..." : "Analyse Patent"}
                    </button>

                    {/* Clear Button */}
                    <button
                      onClick={clearAnalysis}
                      className="custom-btn"
                      disabled={!analysisResult}
                    >
                      Clear
                    </button>
                  </div>
                </>
              )}
            </div>



            {/* AI Suggestions Box */}
            <div className="border rounded-lg shadow-md p-4 bg-white flex flex-col flex-1 min-h-0">
              <div
                className="flex justify-between items-center mb-2 cursor-pointer"
                onClick={() => setIsSuggestionsOpen(!isSuggestionsOpen)}
              >
                <h3 className="font-bold text-lg">AI Suggestions</h3>
                <span>{isSuggestionsOpen ? "▾" : "▸"}</span>
              </div>

              {isSuggestionsOpen && (
                <>
                  {suggestions.length === 0 && (
                    <p className="text-gray-500 text-sm">No suggestions yet</p>
                  )}
                  <div className="flex flex-col gap-2 overflow-y-auto flex-1">
                    {suggestions.map((s, i) => (
                      <div
                        key={i}
                        className="border rounded-lg p-3 bg-white shadow-sm hover:shadow-md transition"
                      >
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-semibold">{s.type}</span>
                          <span className="text-xs text-gray-400">{s.severity}</span>
                        </div>
                        <p className="text-sm mb-1">
                          <strong>Paragraph {s.paragraph}:</strong> {s.description}
                        </p>
                        <p className="text-sm text-blue-600">
                          <em>Suggestion: {s.suggestion}</em>
                        </p>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>


            {/* OVERLAYS */}

            {/* Rewrite Overlay */}
            {rewriteOverlay && (
              <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex justify-center items-center z-50">
                <div className="bg-white p-6 rounded shadow-lg w-[500px] max-w-full">
                  <h4 className="font-bold mb-4 text-lg">AI Rewrite Suggestion</h4>
                  <div className="mb-4">
                    <p className="font-semibold mb-1">Original:</p>
                    <p className="border p-2 rounded text-sm whitespace-pre-wrap">
                      {rewriteOverlay.original}
                    </p>
                  </div>
                  <div className="mb-4">
                    <p className="font-semibold mb-1">Rewritten:</p>
                    <p className="border p-2 rounded text-sm text-blue-700 whitespace-pre-wrap">
                      {rewriteOverlay.rewritten}
                    </p>
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setRewriteOverlay(null)}
                      className="px-3 py-1 rounded border hover:bg-gray-100"
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => {
                        replaceTextInEditor(rewriteOverlay.original, rewriteOverlay.rewritten);
                        setRewriteOverlay(null);

                        showToast(`Changes updated!`);
                      }}
                      className="px-3 py-1 rounded bg-green-600 text-white hover:bg-green-700"
                    >
                      Approve
                    </button>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </div >
    )
  )
}

export default App;