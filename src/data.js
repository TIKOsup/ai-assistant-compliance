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


export const data = {
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
          url: "#",
        },
        {
          title: "Документы",
          url: "#",
        },
        {
          title: "История",
          url: "#",
        },
      ],
    },
  ],
}