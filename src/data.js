import {
  FileUp,
  Bot,
  BookOpen,
  Settings2,
  LifeBuoy,
  Send,
  Frame,
  PieChart,
  Map,
} from "lucide-react";


export let data = {
  user: {
    name: "№404",
    email: "n404team@berekebank.kz",
    avatar: "/src/assets/user-avatar.png",
  },
  navMain: [
    {
      title: "Проверка документов",
      url: "#",
      icon: FileUp,
      isActive: true,
      items: [
        {
          title: "Загрузка PDF",
          url: "upload",
        },
        {
          title: "Документы",
          url: "documents",
        },
        {
          title: "История",
          url: "#",
        },
      ],
    },
  ],
}