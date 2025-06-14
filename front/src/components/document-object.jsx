import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export default function DocumentObject() {
  return (
    <>
      <Card className="m-4">
        <CardHeader>
          <CardTitle>Document Title</CardTitle>
          <CardDescription>Document Size</CardDescription>
          <CardAction>Card Action</CardAction>
        </CardHeader>
      </Card>
    </>
  )
}