// 虚拟模块 - 用于临时运行项目
import React from 'react';

export const Slot = React.forwardRef((props, ref) => React.createElement('div', { ...props, ref }));

// 导出常见的 Radix UI 组件
export const Dialog = (props: any) => <div>{props.children}</div>;
export const DialogContent = (props: any) => <div>{props.children}</div>;
export const DialogTitle = (props: any) => <div>{props.children}</div>;
export const DialogDescription = (props: any) => <div>{props.children}</div>;

export const DropdownMenu = (props: any) => <div>{props.children}</div>;
export const DropdownMenuTrigger = (props: any) => <button>{props.children}</button>;
export const DropdownMenuContent = (props: any) => <div>{props.children}</div>;

export const Popover = (props: any) => <div>{props.children}</div>;
export const PopoverTrigger = (props: any) => <button>{props.children}</button>;
export const PopoverContent = (props: any) => <div>{props.children}</div>;

// 其他常见组件
export const cva = () => () => ({});
export const cn = (...classes: any[]) => classes.filter(Boolean).join(' ');

export const Button = (props: any) => <button {...props}>{props.children}</button>;
export const Input = (props: any) => <input {...props} />;
export const Card = (props: any) => <div {...props}>{props.children}</div>;

// 图标占位
export const SearchIcon = () => <span>🔍</span>;
export const ChevronRightIcon = () => <span>›</span>;
export const CheckIcon = () => <span>✓</span>;
export const CircleIcon = () => <span></span>;