import React, { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Loader2, ArrowUpToLine } from "lucide-react"
import { TypographyH3 } from "./ui/typography"
import { data } from "../table-data"
import { toast } from "sonner"
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerClose,
  DrawerTrigger,
} from "@/components/ui/drawer"

export default function PdfUploader({ setActiveView }) {
  const [pdfFile, setPdfFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(null)
  const [checks, setChecks] = useState({
    compliance: true,
    currControl: true,
  })
  const [file, setFile] = useState(null)
  const [fileUrl, setFileUrl] = useState("")

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file && file.type === "application/pdf") {
      setPdfFile(file)
      setUploadSuccess(null)
      setFile(file)
      const url = URL.createObjectURL(file)
      setFileUrl(url)
    } else {
      alert("Пожалуйста, выберите PDF-файл.")
    }
  }

  const handleToggle = (key) => {
    setChecks((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!pdfFile) return

    const formData = new FormData()
    formData.append("file", pdfFile)
    formData.append("check_compliance", checks.compliance)
    formData.append("check_currControl", checks.currControl)

    console.log(formData)

    setUploading(true)
    setUploadSuccess(null)

    try {
      const res = await fetch("http://localhost:8081/upload", {
        method: "POST",
        body: formData,
      })


      if (!res.ok) throw new Error("Ошибка при загрузке файла");

      const result = await res.json();

      // Сохранение файла
      const fileDetails = {
        id: crypto.randomUUID(),
        name: pdfFile.name,
        date: new Date().toLocaleString("ru-RU"),
        status: result?.status ?? null,
        resultInfo: result?.resultInfo ?? null,
      }
      data.push(fileDetails);
      toast.success("Документ обработан", {
        description: new Date().toLocaleString("ru-RU"),
        action: {
          label: "Перейти",
          onClick: () => setActiveView("documents"),
        },
      });
      setUploadSuccess(true)
    } catch (error) {
      console.error("Ошибка загрузки:", error)
      toast.error("Ошибка при отправке", {
        description: new Date().toLocaleString("ru-RU"),
      });
      setUploadSuccess(false)
    } finally {
      setUploading(false)
    }
  }

  return (
    // <Card className="w-full max-w-md mx-auto mt-8">
    // <CardHeader>
    // <CardTitle>Загрузка документов</CardTitle>
    // </CardHeader>
    // <CardContent className="p-4 space-y-4">
    <div className="w-full max-w-lg mx-auto">
      <TypographyH3>Загрузка документов</TypographyH3>

      <form onSubmit={handleSubmit} className="space-y-4 mt-8">
        <div className="mb-8">
          <Label htmlFor="file" className="mb-4">Выберите PDF файл:</Label>
          <Input id="file" type="file" accept="application/pdf" onChange={handleFileChange} className="cursor-pointer" />
        </div>

        <div className="space-y-2 mb-8">
          <Label className="mb-4">Выберите проверки:</Label>
          <div className="flex flex-col space-y-2 pl-2">
            <div className="flex items-center justify-between">
              <span>Compliance</span>
              <Switch
                checked={checks.compliance}
                onCheckedChange={() => handleToggle("compliance")}
                className="cursor-pointer"
              />
            </div>
            <div className="flex items-center justify-between">
              <span>Валютный контроль</span>
              <Switch
                checked={checks.currControl}
                onCheckedChange={() => handleToggle("currControl")}
                className="cursor-pointer"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-ceter items-center gap-4">
          <Button type="submit" disabled={!pdfFile || uploading} className="cursor-pointer">
            {uploading ? (
              <>
                <Loader2 className="animate-spin w-4 h-4 mr-2" />
                Загрузка...
              </>
            ) : (
              <>
                <ArrowUpToLine className="w-4 h-4 mr-2" />
                Анализировать
              </>
            )}
          </Button>

          <Drawer>
            <DrawerTrigger asChild>
              <Button type="button" disabled={!pdfFile || uploading} className="cursor-pointer">
                Предпросмотр PDF
              </Button>
            </DrawerTrigger>

            <DrawerContent className="h-[90%]">
              <DrawerHeader>
                <DrawerTitle>Предпросмотр PDF</DrawerTitle>
                <DrawerDescription>
                  Загрузите PDF-файл и просмотрите его содержимое ниже
                </DrawerDescription>
              </DrawerHeader>

              <div className="p-4 space-y-4">
                {fileUrl && (
                  <div className="border rounded w-full h-[70vh] overflow-hidden">
                    <iframe
                      src={fileUrl}
                      title="PDF Preview"
                      width="100%"
                      height="100%"
                      className="rounded"
                    />
                  </div>
                )}

                <DrawerClose asChild>
                  <Button variant="outline" className="mt-4">Закрыть</Button>
                </DrawerClose>
              </div>
            </DrawerContent>
          </Drawer>
        </div>
      </form>
    </div>
    // </CardContent>
    // </Card>
  )
}
