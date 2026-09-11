export const api = {} as any;
export type Id<T extends string = string> = string & { __tableName?: T };
