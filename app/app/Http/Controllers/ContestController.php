<?php

namespace App\Http\Controllers;

use App\Http\Requests\ContestStoreRequest;
use App\Http\Requests\ContestUpdateRequest;
use App\Http\Resources\ContestResource;
use App\Models\Contest;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;
use Inertia\Inertia;

class ContestController extends Controller
{
    public function index(Request $request)
    {
        $contests = Contest::query()
            ->with('user')
            ->withCount('contestUsers')
            ->latest()
            ->paginate(10)
            ->withQueryString();

        return Inertia::render('contest/index', [
            'contests' => ContestResource::collection($contests),
        ]);
    }

    // public function create(Request $request): View
    // {
    //     return view('contest.create');
    // }

    // public function store(ContestStoreRequest $request): RedirectResponse
    // {
    //     $contest = Contest::create($request->validated());

    //     $request->session()->flash('contest.id', $contest->id);

    //     return redirect()->route('contests.index');
    // }

    // public function show(Request $request, Contest $contest): View
    // {
    //     return view('contest.show', [
    //         'contest' => $contest,
    //     ]);
    // }

    // public function edit(Request $request, Contest $contest): View
    // {
    //     return view('contest.edit', [
    //         'contest' => $contest,
    //     ]);
    // }

    // public function update(ContestUpdateRequest $request, Contest $contest): RedirectResponse
    // {
    //     $contest->update($request->validated());

    //     $request->session()->flash('contest.id', $contest->id);

    //     return redirect()->route('contests.index');
    // }

    // public function destroy(Request $request, Contest $contest): RedirectResponse
    // {
    //     $contest->delete();

    //     return redirect()->route('contests.index');
    // }
}
