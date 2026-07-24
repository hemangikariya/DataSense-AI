"use client"

import React, { useEffect, useState } from "react"
import DashboardLayout from "@/components/layout/dashboard-layout"
import { userApi } from "@/lib/user-api"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as zod from "zod"
import { Button, Input, Card, Tabs } from "@/components/common/components"
import { ShieldAlert, CheckCircle2, Camera } from "lucide-react"

// Schemas
const profileSchema = zod.object({
  first_name: zod.string().min(1, "First name is required."),
  last_name: zod.string().min(1, "Last name is required."),
  phone: zod.string().optional()
})

const passwordSchema = zod.object({
  current_password: zod.string().min(1, "Current password is required."),
  new_password: zod.string().min(8, "New password must be at least 8 characters long.")
})

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  
  const [profileMsg, setProfileMsg] = useState("")
  const [profileError, setProfileError] = useState("")

  const [passwordMsg, setPasswordMsg] = useState("")
  const [passwordError, setPasswordError] = useState("")

  const [avatarLoading, setAvatarLoading] = useState(false)

  const {
    register: registerProfile,
    handleSubmit: handleSubmitProfile,
    reset: resetProfile
  } = useForm({
    resolver: zodResolver(profileSchema)
  })

  const {
    register: registerPassword,
    handleSubmit: handleSubmitPassword,
    reset: resetPassword
  } = useForm({
    resolver: zodResolver(passwordSchema)
  })

  const loadProfile = async () => {
    try {
      const data = await userApi.getProfile()
      setProfile(data)
      resetProfile({
        first_name: data.first_name,
        last_name: data.last_name,
        phone: data.phone || ""
      })
    } catch (err) {
      console.error("Failed to load user profile context.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProfile()
  }, [])

  const onUpdateProfile = async (data: any) => {
    setProfileMsg("")
    setProfileError("")
    try {
      const res = await userApi.updateProfile(data)
      setProfile(res)
      setProfileMsg("Profile updated successfully!")
    } catch (err: any) {
      setProfileError(err.response?.data?.detail || "Failed to update profile.")
    }
  }

  const onChangePassword = async (data: any) => {
    setPasswordMsg("")
    setPasswordError("")
    try {
      await userApi.changePassword(data)
      setPasswordMsg("Password changed successfully!")
      resetPassword()
    } catch (err: any) {
      setPasswordError(err.response?.data?.detail || "Current password check failed.")
    }
  }

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setAvatarLoading(true)
    try {
      const res = await userApi.uploadAvatar(file)
      setProfile((prev: any) => ({ ...prev, avatar_url: res.avatar_url }))
      // Update local storage user details
      const cached = localStorage.getItem("user")
      if (cached) {
        const u = JSON.parse(cached)
        u.avatar_url = res.avatar_url
        localStorage.setItem("user", JSON.stringify(u))
      }
    } catch (err) {
      console.error("Avatar upload failed.")
    } finally {
      setAvatarLoading(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="p-8 space-y-6">
          <div className="h-6 bg-slate-800 rounded w-1/4 animate-pulse" />
          <div className="grid grid-cols-1 gap-6">
            <div className="h-40 bg-slate-800 rounded animate-pulse" />
          </div>
        </div>
      </DashboardLayout>
    )
  }

  const profileTabContent = (
    <Card className="space-y-6">
      <div className="flex flex-col sm:flex-row items-center gap-6 pb-6 border-b border-slate-850">
        <div className="relative group">
          <div className="w-20 h-20 bg-blue-600 rounded-full overflow-hidden flex items-center justify-center text-xl font-bold uppercase text-white border-2 border-slate-800">
            {profile?.avatar_url ? (
              <img src={profile.avatar_url} alt="Profile photo" className="w-full h-full object-cover" />
            ) : (
              <span>{profile?.email?.[0] || "U"}</span>
            )}
          </div>
          <label className="absolute bottom-0 right-0 bg-slate-900 border border-slate-800 hover:bg-slate-850 p-1.5 rounded-full cursor-pointer transition shadow">
            <Camera className="w-3.5 h-3.5 text-slate-400" />
            <input type="file" onChange={handleAvatarChange} className="hidden" accept="image/*" disabled={avatarLoading} />
          </label>
        </div>

        <div className="flex-1 text-center sm:text-left space-y-1">
          <h2 className="text-sm font-bold text-slate-200">{profile?.first_name} {profile?.last_name}</h2>
          <p className="text-[10px] text-slate-400">{profile?.email}</p>
          <div className="inline-block px-2.5 py-0.5 rounded text-[8px] font-semibold bg-blue-500/10 text-blue-400 uppercase mt-2">
            {profile?.org_role || "Analyst"}
          </div>
        </div>
      </div>

      {profileMsg && (
        <div className="p-3 bg-green-500/10 border border-green-500/20 text-green-400 text-xs rounded">
          {profileMsg}
        </div>
      )}

      {profileError && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 text-xs rounded">
          {profileError}
        </div>
      )}

      <form onSubmit={handleSubmitProfile(onUpdateProfile)} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input label="First Name" {...registerProfile("first_name")} required />
          <Input label="Last Name" {...registerProfile("last_name")} required />
        </div>
        <Input label="Phone Number" {...registerProfile("phone")} placeholder="+1 (555) 019-2834" />
        
        <div className="flex justify-end pt-2">
          <Button type="submit">Save Changes</Button>
        </div>
      </form>
    </Card>
  )

  const securityTabContent = (
    <Card className="space-y-6">
      <div>
        <h3 className="text-xs font-bold text-slate-200 uppercase">Change Password</h3>
        <p className="text-[10px] text-slate-400 mt-1">Ensure your account keys are rotated periodically.</p>
      </div>

      {passwordMsg && (
        <div className="p-3 bg-green-500/10 border border-green-500/20 text-green-400 text-xs rounded">
          {passwordMsg}
        </div>
      )}

      {passwordError && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 text-xs rounded">
          {passwordError}
        </div>
      )}

      <form onSubmit={handleSubmitPassword(onChangePassword)} className="space-y-4">
        <Input type="password" label="Current Password" {...registerPassword("current_password")} required />
        <Input type="password" label="New Password" {...registerPassword("new_password")} required />
        
        <div className="flex justify-end pt-2">
          <Button type="submit">Update Password</Button>
        </div>
      </form>
    </Card>
  )

  const tabsConfig = [
    { value: "profile", label: "Profile Info", content: profileTabContent },
    { value: "security", label: "Security & Keys", content: securityTabContent }
  ]

  return (
    <DashboardLayout>
      <div className="p-8 space-y-6 max-w-3xl">
        <div>
          <h1 className="text-xl font-bold tracking-tight">User Account</h1>
          <p className="text-slate-400 text-xs mt-1">
            Update personal info, security preferences, or upload avatars.
          </p>
        </div>

        <Tabs tabs={tabsConfig} />
      </div>
    </DashboardLayout>
  )
}
