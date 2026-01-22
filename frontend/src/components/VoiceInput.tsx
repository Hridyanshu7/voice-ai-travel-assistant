"use client";

import React, { useState, useRef } from "react";
import { Mic, Square, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface VoiceInputProps {
    onTranscriptChange: (transcript: string) => void;
}

export function VoiceInput({ onTranscriptChange }: VoiceInputProps) {
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                setIsProcessing(true);
                const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
                await sendAudioToBackend(audioBlob);
                setIsProcessing(false);
                setIsRecording(false);

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            setIsRecording(true);
            onTranscriptChange(""); // Clear previous

        } catch (err) {
            console.error("Error accessing microphone:", err);
            alert("Could not access microphone. Please ensure permissions are granted.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
        }
    };

    const sendAudioToBackend = async (audioBlob: Blob) => {
        try {
            const formData = new FormData();
            formData.append("file", audioBlob, "recording.webm");

            const response = await fetch("http://localhost:8000/api/transcribe", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error("STT Backend Error:", errorText);
                throw new Error(`Server error: ${response.statusText} - ${errorText}`);
            }

            const data = await response.json();
            const text = data.transcript;
            onTranscriptChange(text);

        } catch (error) {
            console.error("Transcription error:", error);
            onTranscriptChange("Error: Could not transcribe audio.");
        }
    };

    const toggleRecording = () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    return (
        <button
            onClick={toggleRecording}
            disabled={isProcessing}
            className={cn(
                "p-2 rounded-full transition-all duration-300",
                isRecording
                    ? "text-red-500 hover:text-red-600 animate-pulse"
                    : "text-blue-600 hover:text-blue-700",
                isProcessing && "text-slate-400 cursor-not-allowed"
            )}
            aria-label={isRecording ? "Stop recording" : "Start recording"}
            title={isRecording ? "Stop recording" : "Start voice input"}
        >
            {isProcessing ? (
                <Loader2 className="w-5 h-5 animate-spin" />
            ) : isRecording ? (
                <Square className="w-5 h-5" />
            ) : (
                <Mic className="w-5 h-5" />
            )}
        </button>
    );
}
