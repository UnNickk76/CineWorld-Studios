// CineWorld Studio's - Shared imports for all pages
// Re-exports commonly used dependencies to reduce boilerplate

// React core
export { default as React, useState, useEffect, useRef, useCallback, useMemo, useContext } from 'react';
export { useNavigate, useLocation, useSearchParams, useParams } from 'react-router-dom';

// UI Components
export { Button } from '../components/ui/button';
export { Input } from '../components/ui/input';
export { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
export { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
export { Badge } from '../components/ui/badge';
export { Progress } from '../components/ui/progress';
export { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
export { ScrollArea } from '../components/ui/scroll-area';
export { Slider } from '../components/ui/slider';
export { Textarea } from '../components/ui/textarea';
export { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription, DialogFooter } from '../components/ui/dialog';
export { Label } from '../components/ui/label';
export { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
export { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '../components/ui/alert-dialog';
export { Checkbox } from '../components/ui/checkbox';
export { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';

// External
export { toast } from 'sonner';
export { motion, AnimatePresence } from 'framer-motion';
export { format } from 'date-fns';

// Contexts
export { AuthContext, LanguageContext, useTranslations, PlayerPopupContext, usePlayerPopup } from '../contexts';

// Constants
export { SKILL_TRANSLATIONS } from '../constants';
