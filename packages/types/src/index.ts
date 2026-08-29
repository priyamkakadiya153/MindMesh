import { z } from 'zod';

// ==========================================
// TypeScript DTOs & Types
// ==========================================

export interface UserDTO {
  id: string;
  phoneNumber: string;
  role: 'OWNER' | 'ADMIN' | 'MEMBER';
  createdAt: Date;
  updatedAt: Date;
}

export interface MessageDTO {
  id: string;
  roomId: string;
  senderId: string;
  content: string;
  isFile: boolean;
  fileId?: string | null;
  createdAt: Date;
}

export interface RoomDTO {
  id: string;
  name?: string | null;
  type: 'ONE_TO_ONE' | 'GROUP';
  createdAt: Date;
  updatedAt: Date;
}

// ==========================================
// Zod Validation Schemas
// ==========================================

// Auth validation
export const SendOtpSchema = z.object({
  phoneNumber: z.string().regex(/^\+?[1-9]\d{1,14}$/, {
    message: 'Invalid phone number format. Must match E.164 standards.',
  }),
});

export const VerifyOtpSchema = z.object({
  phoneNumber: z.string().regex(/^\+?[1-9]\d{1,14}$/, {
    message: 'Invalid phone number format.',
  }),
  code: z.string().length(6, {
    message: 'OTP must be exactly 6 digits.',
  }),
});

// Chat validation
export const SendMessageSchema = z.object({
  roomId: z.string().uuid(),
  content: z.string().min(1, { message: 'Message content cannot be empty.' }),
  isFile: z.boolean().default(false),
  fileId: z.string().uuid().optional(),
});

export const CreateRoomSchema = z.object({
  name: z.string().min(3).max(50).optional(),
  type: z.enum(['ONE_TO_ONE', 'GROUP']),
  userIds: z.array(z.string().uuid()).min(1, {
    message: 'At least one participant must be specified.',
  }),
});

// Types inferred from Zod schemas
export type SendOtpInput = z.infer<typeof SendOtpSchema>;
export type VerifyOtpInput = z.infer<typeof VerifyOtpSchema>;
export type SendMessageInput = z.infer<typeof SendMessageSchema>;
export type CreateRoomInput = z.infer<typeof CreateRoomSchema>;
