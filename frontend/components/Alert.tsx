type AlertProps = {
  title: string;
  message: string;
};

export function Alert({ title, message }: AlertProps) {
  return (
    <div className="rounded-lg border border-coral/35 bg-coral/10 p-4 text-sm text-ink dark:text-mist">
      <p className="font-semibold text-coral">{title}</p>
      <p className="mt-1 leading-6">{message}</p>
    </div>
  );
}
