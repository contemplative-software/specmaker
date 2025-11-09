# Todo List Next.js App — Implementation Plan

## Overview

Create a simple todo list application with Next.js featuring basic CRUD operations to demonstrate component composition and state management.

## Requirements

### Tech Stack
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS for styling
- React hooks for state management

### Features
- Add new todo items with text input
- Mark todos as complete/incomplete
- Delete todo items
- Display list of all todos
- Responsive design with clean UI
- Local state management (no database)

### Scope
No backend API, no persistence, no authentication — just client-side state management with CRUD operations.

## Implementation Phases

### Phase 0 — Project Initialization
- Initialize Next.js project with TypeScript and Tailwind
- Configure TypeScript and Tailwind CSS
- Set up basic project structure
- Exit criteria: `npm run dev` starts successfully

### Phase 1 — Data Model & Types
- Define Todo interface with id, text, and completed properties
- Create type definitions for component props
- Exit criteria: TypeScript types defined without errors

### Phase 2 — Core Components
- Create TodoItem component for individual todo display
- Create AddTodo component with input form
- Create TodoList component to orchestrate state and rendering
- Exit criteria: All components render without errors

### Phase 3 — CRUD Operations
- Implement add todo functionality
- Implement toggle complete functionality
- Implement delete todo functionality
- Exit criteria: All operations work correctly

### Phase 4 — Styling & Polish
- Apply Tailwind styling for modern look
- Add hover states and transitions
- Implement responsive design
- Add empty state message
- Exit criteria: UI looks polished and responsive

### Phase 5 — Documentation & Validation
- Add README with setup and run instructions
- Verify build and type checking passes
- Test all CRUD operations
- Exit criteria: `npm run build` succeeds

## Project Structure

```
todo-list-nextjs/
├── app/
│   ├── layout.tsx      # Root layout with metadata
│   ├── page.tsx        # Main page with TodoList
│   └── globals.css     # Tailwind imports
├── components/
│   ├── TodoList.tsx    # Main container with state
│   ├── TodoItem.tsx    # Individual todo item
│   └── AddTodo.tsx     # Input form for new todos
├── types/
│   └── todo.ts         # Todo type definitions
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── README.md
```

## Code Examples

### Todo Type Definition (types/todo.ts)
```typescript
export interface Todo {
  id: string;
  text: string;
  completed: boolean;
}
```

### TodoList Component (components/TodoList.tsx)
```typescript
"use client";

import { useState } from "react";
import { Todo } from "@/types/todo";
import TodoItem from "./TodoItem";
import AddTodo from "./AddTodo";

export default function TodoList() {
  const [todos, setTodos] = useState<Todo[]>([]);

  const addTodo = (text: string) => {
    const newTodo: Todo = {
      id: crypto.randomUUID(),
      text,
      completed: false,
    };
    setTodos([...todos, newTodo]);
  };

  const toggleTodo = (id: string) => {
    setTodos(todos.map(todo =>
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
  };

  const deleteTodo = (id: string) => {
    setTodos(todos.filter(todo => todo.id !== id));
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">My Todo List</h1>
      <AddTodo onAdd={addTodo} />
      <div className="mt-6 space-y-2">
        {todos.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No todos yet. Add one above!
          </p>
        ) : (
          todos.map(todo => (
            <TodoItem
              key={todo.id}
              todo={todo}
              onToggle={toggleTodo}
              onDelete={deleteTodo}
            />
          ))
        )}
      </div>
    </div>
  );
}
```

### TodoItem Component (components/TodoItem.tsx)
```typescript
import { Todo } from "@/types/todo";

interface TodoItemProps {
  todo: Todo;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function TodoItem({ todo, onToggle, onDelete }: TodoItemProps) {
  return (
    <div className="flex items-center gap-3 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
      <input
        type="checkbox"
        checked={todo.completed}
        onChange={() => onToggle(todo.id)}
        className="w-5 h-5 rounded border-gray-300"
      />
      <span className={`flex-1 ${todo.completed ? "line-through text-gray-400" : ""}`}>
        {todo.text}
      </span>
      <button
        onClick={() => onDelete(todo.id)}
        className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
      >
        Delete
      </button>
    </div>
  );
}
```

### AddTodo Component (components/AddTodo.tsx)
```typescript
"use client";

import { useState } from "react";

interface AddTodoProps {
  onAdd: (text: string) => void;
}

export default function AddTodo({ onAdd }: AddTodoProps) {
  const [text, setText] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      onAdd(text.trim());
      setText("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="What needs to be done?"
        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        type="submit"
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Add
      </button>
    </form>
  );
}
```

### Main Page (app/page.tsx)
```typescript
import TodoList from "@/components/TodoList";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
      <TodoList />
    </main>
  );
}
```

## Validation Checklist

- [ ] `npm install` completes without errors
- [ ] `npm run dev` starts on port 3000
- [ ] Can add new todo items
- [ ] Can mark todos as complete/incomplete
- [ ] Can delete todo items
- [ ] Empty state displays when no todos
- [ ] `npm run build` builds successfully
- [ ] `npx tsc --noEmit` passes type checking
- [ ] UI is responsive on mobile and desktop
- [ ] All components follow TypeScript best practices

## Success Criteria

✅ Project initializes and installs dependencies  
✅ Development server runs without errors  
✅ All CRUD operations work correctly  
✅ State management updates UI properly  
✅ TypeScript types are properly defined  
✅ Components are properly separated by concern  
✅ Styling is clean and responsive  
✅ Build completes successfully  
✅ README documents all commands

