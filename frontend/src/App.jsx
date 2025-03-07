import { useState, useEffect } from "react";
import axios from "axios";
import { motion } from "framer-motion";

const API_URL = "http://localhost:8000"

export default function App() {
    const [username, setUsername] = useState("");
    const [code, setCode] = useState("");
    const [language, setLanguage] = useState("python");
    const [result, setResult] = useState(null);
    const [leaderboard, setLeaderboard] = useState([]);
    const [loading, setLoading] = useState(false);
    const [optimizedCode, setOptimizedCode] = useState("");
    const [error, setError] = useState(null);

    const languages = ["python", "javascript", "java", "cpp"];

    useEffect(() => {
        fetchLeaderboard();
    }, []);

    const fetchLeaderboard = async () => {
        try {
            const response = await axios.get(`${API_URL}/leaderboard`);
            setLeaderboard(response.data.leaderboard || []);
        } catch (err) {
            console.error("Error fetching leaderboard:", err);
            setError("Failed to fetch leaderboard.");
        }
    };

    const submitCode = async () => {
        if (!username.trim()) {
            setError("Please enter a username.");
            return;
        }
        if (!code.trim()) {
            setError("Please enter some code.");
            return;
        }

        setLoading(true);
        setResult(null);
        setOptimizedCode("");
        setError(null);

        try {
            const response = await axios.post(`${API_URL}/analyze`, {
                username,
                code,
                language,
            });

            if (response.data.error) {
                setError(response.data.error);
            } else {
                setResult(response.data);
                fetchLeaderboard();
            }
        } catch (err) {
            setError("Failed to analyze code. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const requestOptimization = async () => {
        try {
            const response = await axios.post(`${API_URL}/optimize`, {
                username,
                code,
                language,
            });

            if (response.data.optimized_code) {
                setOptimizedCode(response.data.optimized_code);
            } else {
                setError("Failed to retrieve optimized code.");
            }
        } catch (err) {
            setError("Optimization request failed.");
        }
    };

    return (
        <div className="min-h-screen w-full bg-gray-800 text-white flex flex-col items-center p-6">
            {/* Leaderboard */}
            <h1 className="text-3xl font-bold mb-4 text-center">🏆 Leaderboard 🏆</h1>
            <div className="grid grid-cols-3 gap-4 mb-6 w-full max-w-4xl">
                {leaderboard.length > 0 ? (
                    leaderboard.map((entry, index) => (
                        <motion.div
                            key={index}
                            className="bg-gray-800 p-3 rounded-lg text-center font-semibold"
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 * index }}
                        >
                            {entry.username} - {entry.score} pts
                        </motion.div>
                    ))
                ) : (
                    <p className="col-span-3 text-center text-gray-500">No leaderboard data yet.</p>
                )}
            </div>

            {/* Username Input */}
            <input
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full max-w-4xl p-3 bg-gray-900 border border-gray-600 rounded-lg text-lg text-white placeholder-gray-400 mb-4"
            />

            {/* Code Input */}
            <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full max-w-4xl p-4 bg-gray-900 border border-gray-600 rounded-lg text-lg font-mono text-white placeholder-gray-400"
                placeholder="Paste your code snippet here..."
                rows="6"
            />

            {/* Language Selector and Submit Button */}
            <div className="flex justify-between items-center mt-4 w-full max-w-4xl">
                <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="p-3 border rounded-lg bg-gray-800 text-white"
                >
                    {languages.map((lang) => (
                        <option key={lang} value={lang}>
                            {lang.toUpperCase()}
                        </option>
                    ))}
                </select>

                <button
                    onClick={submitCode}
                    className="bg-blue-500 text-white px-6 py-3 rounded-lg shadow-md transition hover:bg-blue-600"
                >
                    Submit
                </button>
            </div>

            {/* Show Errors */}
            {error && (
                <motion.div
                    className="mt-6 p-4 bg-red-500 text-white rounded-lg"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                >
                     {error}
                </motion.div>
            )}

            {/* Loading State */}
            {loading && <p className="text-center mt-4">🔄 Processing...</p>}

            {/* Result */}
            {result && !error && (
                <motion.div
                    className="mt-6 p-4 bg-gray-800 rounded-lg max-w-4xl w-full"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                >
                    <h2 className="text-lg font-bold">💡 Readability Score: {result.readability_score || "N/A"}</h2>
                    <p className="mt-2">⏳ Runtime: {result.runtime || "N/A"}</p>
                    <p>📦 Memory Usage: {result.memory || "N/A"}</p>
                    {result.suggestions && result.suggestions.length > 0 ? (
                        <ul className="mt-2">
                            {result.suggestions.map((suggestion, i) => (
                                <li key={i} className="text-red-400"> {suggestion}</li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-gray-500 mt-2">✅ No suggestions found.</p>
                    )}

                    <button
                        onClick={requestOptimization}
                        className="mt-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-md transition hover:bg-green-600"
                    >
                        Optimize Code
                    </button>
                </motion.div>
            )}

            {/* Optimized Code */}
            {optimizedCode && !error && (
                <motion.div
                    className="mt-6 p-4 bg-green-800 rounded-lg font-mono max-w-4xl w-full"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                >
                    <h2 className="text-lg font-bold">✨ Optimized Code</h2>
                    <pre className="mt-2">{optimizedCode}</pre>
                </motion.div>
            )}
        </div>
    );
}
