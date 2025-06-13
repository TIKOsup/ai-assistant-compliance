"use client"

import React, { useState } from "react"
import { Drawer, DrawerTrigger, DrawerContent, DrawerHeader, DrawerTitle, DrawerDescription, DrawerClose } from "@/components/ui/drawer"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function PdfDrawerPreview() {
  const [file, setFile] = useState(null)
  const [fileUrl, setFileUrl] = useState("")

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0]
    if (selected?.type === "application/pdf") {
      setFile(selected)
      const url = URL.createObjectURL(selected)
      setFileUrl(url)
    } else {
      alert("Пожалуйста, выберите PDF-файл.")
    }
  }

  return (
    <Drawer>
      <DrawerTrigger asChild>
        <Button>Предпросмотр PDF</Button>
      </DrawerTrigger>

      <DrawerContent className="h-[90%]">
        <DrawerHeader>
          <DrawerTitle>Предпросмотр PDF</DrawerTitle>
          <DrawerDescription>
            Загрузите PDF-файл и просмотрите его содержимое ниже
          </DrawerDescription>
        </DrawerHeader>

        <div className="p-4 space-y-4">
          <div>
            <Label htmlFor="pdf">Файл PDF:</Label>
            <Input id="pdf" type="file" accept="application/pdf" onChange={handleFileChange} />
          </div>

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
  )
}