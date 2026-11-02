import { useState, useRef, useCallback, useEffect } from 'react'

export function useVoiceInput(onResult: (text: string) => void) {
  const [listening, setListening] = useState(false)
  const [supported, setSupported] = useState(true)
  const recognitionRef = useRef<any>(null)
  const listeningRef = useRef(false)

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (!SpeechRecognition) {
      setSupported(false)
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0]?.transcript ?? '')
        .join('')
        .trim()
      if (transcript) onResult(transcript)
    }

    recognition.onend = () => {
      listeningRef.current = false
      setListening(false)
    }

    recognition.onerror = () => {
      listeningRef.current = false
      setListening(false)
    }

    recognitionRef.current = recognition
    return () => {
      listeningRef.current = false
      try { recognition.stop() } catch { /* already stopped */ }
      recognitionRef.current = null
    }
  }, [onResult])

  const start = useCallback(() => {
    const recognition = recognitionRef.current
    if (!recognition || listeningRef.current) return
    try {
      recognition.start()
      listeningRef.current = true
      setListening(true)
    } catch (error) {
      // Browsers throw if recognition is already active; keep the UI stable.
      console.warn('Could not start voice recognition:', error)
    }
  }, [])

  const stop = useCallback(() => {
    const recognition = recognitionRef.current
    if (!recognition || !listeningRef.current) return
    listeningRef.current = false
    setListening(false)
    try { recognition.stop() } catch { /* already stopped */ }
  }, [])

  const toggle = useCallback(() => {
    if (listeningRef.current) stop()
    else start()
  }, [start, stop])

  return { listening, supported, start, stop, toggle }
}
