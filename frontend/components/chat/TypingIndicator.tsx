import { BrainCircuit } from "lucide-react";
import { motion } from "framer-motion";

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 px-4 md:px-8 py-2 w-full mt-2">
      <div className="max-w-3xl flex gap-4 w-full">
        <div className="w-8 flex justify-center mt-1">
          <BrainCircuit size={16} className="text-accent animate-pulse" />
        </div>
        <motion.div 
          initial={{ opacity: 0.5 }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="text-sm text-text-secondary italic flex items-center"
        >
          Agent Zouglou réfléchit...
        </motion.div>
      </div>
    </div>
  );
}
