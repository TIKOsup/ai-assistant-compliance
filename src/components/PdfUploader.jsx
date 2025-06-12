import React, { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2, UploadCloud } from "lucide-react"

export default function PdfUploader() {
  const [pdfFile, setPdfFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(null)

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file && file.type === "application/pdf") {
      setPdfFile(file)
      setUploadSuccess(null)
    } else {
      alert("Пожалуйста, выберите PDF-файл.")
    }
  }

  const uploadToServer = async () => {
    if (!pdfFile) return

    const formData = new FormData()
    formData.append("file", pdfFile)

    setUploading(true)
    setUploadSuccess(null)

    try {
      const res = await fetch("/api/upload-pdf", {
        method: "POST",
        body: formData,
      })

      if (!res.ok) throw new Error("Ошибка при загрузке файла")

      setUploadSuccess(true)
    } catch (error) {
      console.error("Ошибка загрузки:", error)
      setUploadSuccess(false)
    } finally {
      setUploading(false)
    }
  }

  return (
    <Card className="w-full max-w-md mx-auto mt-8">
      <CardContent className="p-4 space-y-4">
        <Input type="file" accept="application/pdf" onChange={handleFileChange} />

        {pdfFile && (
          <div className="flex items-center gap-4">
            <Button onClick={uploadToServer} disabled={uploading}>
              {uploading ? (
                <>
                  <Loader2 className="animate-spin w-4 h-4 mr-2" />
                  Загрузка...
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4 mr-2" />
                  Отправить на сервер
                </>
              )}
            </Button>

            {uploadSuccess === true && <p className="text-green-600">Успешно загружено</p>}
            {uploadSuccess === false && <p className="text-red-600">Ошибка загрузки</p>}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
