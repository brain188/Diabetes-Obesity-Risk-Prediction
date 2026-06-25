import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { useCreatePatient } from "@/hooks/usePatients";

const minDob = () => {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 18);
  return d;
};

const schema = z.object({
  full_name: z.string().min(2, "Full name is required"),
  date_of_birth: z
    .string()
    .min(1, "Date of birth is required")
    .refine((val) => new Date(val) <= minDob(), "Patient must be at least 18 years old"),
  sex: z.enum(["Male", "Female"], { required_error: "Sex is required" }),
  contact_info: z.string().optional(),
  national_id: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
}

export function RegisterPatientDialog({ open, onClose }: Props) {
  const create = useCreatePatient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = (data: FormValues) => {
    create.mutate(data, {
      onSuccess: () => {
        toast.success("Patient registered successfully.");
        reset();
        onClose();
      },
      onError: () => toast.error("Failed to register patient. Please try again."),
    });
  };

  const field =
    "w-full px-3 py-2 bg-card border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all";
  const label = "block text-sm font-medium text-foreground mb-1.5";
  const err = "mt-1 text-xs text-destructive";

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Register New Patient</DialogTitle>
          <DialogDescription>Enter the patient's details to create their clinical record.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-2">
          <div>
            <label className={label}>Full Name *</label>
            <input {...register("full_name")} placeholder="e.g. Jane Doe" className={field} />
            {errors.full_name && <p className={err}>{errors.full_name.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={label}>Date of Birth *</label>
              <input
                {...register("date_of_birth")}
                type="date"
                max={minDob().toISOString().split("T")[0]}
                className={field}
              />
              {errors.date_of_birth && <p className={err}>{errors.date_of_birth.message}</p>}
            </div>
            <div>
              <label className={label}>Sex *</label>
              <select {...register("sex")} className={field}>
                <option value="">Select…</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
              {errors.sex && <p className={err}>{errors.sex.message}</p>}
            </div>
          </div>

          <div>
            <label className={label}>Contact Info</label>
            <input {...register("contact_info")} placeholder="+237 6xx xxx xxx" className={field} />
          </div>

          <div>
            <label className={label}>National ID</label>
            <input {...register("national_id")} placeholder="Optional" className={field} />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => { reset(); onClose(); }}
              className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={create.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-60 transition-colors"
            >
              {create.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Register Patient
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
