import ChatInterface from "@/components/chat-interface";

export default function ChatPage() {
  return (
    <div className="h-full flex flex-col">
      <div className="px-8 py-6 border-b border-gray-200 bg-white">
        <h2 className="text-xl font-bold text-gray-900">Chat</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Ask questions about your spending patterns and financial habits.
        </p>
      </div>
      <div className="flex-1 overflow-hidden">
        <ChatInterface />
      </div>
    </div>
  );
}
