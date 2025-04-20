---
layout: post
title: Post-Dual Boot Cleanup – Reclaiming Lost Partition Space After Removing Ubuntu
date: 2025-04-20 21:00 +0530
categories: [system, fix]
tags: [dual-boot, gparted, partition, unallocated-space, disk-management, partition-recovery, ubuntu-removal, recover-space, efi-boot, system-partition, live-usb, kali-linux, ubuntu-live, diskpart-error]
---

# Post-Dual Boot Cleanup – Reclaiming Lost Partition Space After Removing Ubuntu

## Introduction

This isn't my usual post about **vulnerabilities**, **bug bounty**, or **web security**. This time, it's something different — a persistent issue I hit after removing Ubuntu from a dual-boot setup. It messed up my partitions, left behind EFI boot entries, and blocked nearly **100 GB of usable space**.

After trying several tools and commands (many of which failed), I finally resolved it — so here's a write-up for anyone facing the same frustrating post-dual-boot cleanup.

## The Problem

After removing Ubuntu:
- I still saw **Ubuntu** entries in my UEFI boot menu
- **Disk Management** in Windows showed a **1.07 GB System partition**, 98 GB of **unallocated space**, and wouldn't let me extend the main partition
- `diskpart` couldn't delete the partition: `Virtual Disk Service error: The operation is not supported by the object.`
- Tools like **MiniTool Partition Wizard** didn't help
- **WSL** showed disk usage but wasn't able to manipulate partitions

## The Solution: Using a Live Linux Environment

Since Windows tools couldn't fix the partition issues, I needed to approach the problem from outside Windows. **A Linux live boot environment** provides the perfect tools for this job, particularly GParted, which has more powerful partition management capabilities than Windows Disk Management.

For this guide, I used **Kali Linux** as my live USB distro (because I keep it around for security testing), but this solution will work equally well with **Ubuntu Live**, **GParted Live**, or any Linux ISO that includes GParted.

## Step-by-Step Fix

### 1. Disable Secure Boot

Booting into Kali or any unsigned Linux ISO often fails with a "Security Violation" error. To fix that:
- Enter BIOS (usually `F2`, `DEL`, or `ESC` on boot)
- Disable **Secure Boot**
- Save and exit

### 2. Create Live USB (I Used Kali)

- I used **Rufus** with the following options:
  - **Partition scheme**: GPT
  - **Target system**: UEFI (non-CSM)
  - **File system**: FAT32
- You can use Ubuntu, GParted Live, etc., but I used Kali just in case I needed other tools

### 3. Boot Kali and Open GParted

Once Kali booted:
- Open **GParted**
- I noticed:
  - A ~1.x GB "System" partition
  - ~98.x GB of **unallocated space** that couldn't be used because the system partition was in the way

> Windows couldn't remove that system partition, but GParted could.

### 4. Delete the System Partition

- Right-clicked the 1.x GB "System" partition
- Selected **Delete**
- Now I had one large ~100 GB chunk of unallocated space

### 5. Resize the Existing Partition

- Right-clicked the main (E:) partition
- Selected **Resize/Move**
- Dragged to use **all the available unallocated space**
- Set **Align to** → `MiB` (recommended)
- Applied changes using the **green checkmark**

### 6. Merge in Windows (Disk Management)

- Rebooted into Windows
- Opened **Disk Management** (`diskmgmt.msc`)
- The previously unallocated 100 GB was now directly next to my E: drive
- Right-clicked the partition → **Extend Volume...**
- Merged the space successfully — no tools needed

## Conclusion

Post-dual boot cleanup can get tricky when partitions are locked, out of order, or marked as system-reserved — especially when Windows tools refuse to cooperate. The key takeaway here is: **sometimes the only way to reclaim your space is from outside Windows**.

While I personally used **Kali Linux** as my live USB (mostly because I keep it around for security testing), you don't have to. This method works just as well with **Ubuntu Live**, **GParted Live**, or any Linux distro that includes GParted.

In the end, combining GParted for surgical cleanup and Windows Disk Management for finishing touches gave me a clean, single-boot setup with all my space back — no formatting, no reinstalls, no stress.

Got a similar mess? Boot live, take control, and reclaim your space.